from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any
import asyncio


from app.models.chat_model import(
    ChatRequest,ChatResponse, DxfRequest, DesignFileRequest,
    CreateSessionRequest, UpdateSessionTitleRequest, MessageFeedbackRequest
)

from app.compliance.models import LayoutExtract
from app.compliance.extraction_fallback import merge_heuristic_layout
from app.compliance.validator import parse_layout_from_llm_dict, validate_us_irc_baseline
from app.services.cadllm_service import cadllm_service
from app.services.gemini_service import gemini_service
from app.services.chat_history_service import chat_history_service
from app.services.subscription_service import subscription_service
from app.core.config import settings
import logging
import os
import uuid

from app.middlewares.auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)

# One DWG conversion at a time per worker (ODA+Xvfb is heavy; parallel runs cause timeouts).
_dwg_convert_lock = asyncio.Lock()


@router.post("/chat/dxf")
async def generate_dxf(request: DxfRequest, user_data: dict = Depends(require_auth)):
    """
    Generates a DXF file from an image URL.
    Uses External Service (Api2Convert) for high-fidelity Raster-to-Vector conversion.
    """
    try:
        # Validate auth
        user_id = user_data["user_id"] 
        
        from app.services.local_dxf_service import local_dxf_service
        logger.info("Requesting Local DXF Conversion (Potrace)...")
        file_path = await local_dxf_service.convert_to_dxf(request.image_url)

        # Check and Return
        if not os.path.exists(file_path):
             raise HTTPException(status_code=500, detail="Failed to retrieve DXF file from external provider")

        return FileResponse(
            path=file_path, 
            filename=os.path.basename(file_path),
            media_type='application/dxf'
        )

    except Exception as e:
        logger.error(f"DXF Generation Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _safe_unlink(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.unlink(path)
    except Exception:
        pass


def _safe_rmtree(path: str) -> None:
    try:
        if path and os.path.exists(path):
            import shutil
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


@router.post("/chat/design-file")
async def generate_design_file(
    request: DesignFileRequest,
    background: BackgroundTasks,
    user_data: dict = Depends(require_auth),
):
    """
    Generate a design file from an image URL.

    - file_type="dxf": raster → DXF (Potrace) and downloads
    - file_type="dwg": raster → DXF (Potrace) → DWG (external converter) and downloads
    """
    try:
        _ = user_data["user_id"]  # validate auth context

        file_type = (request.file_type or "").strip().lower()
        if file_type not in ("dxf", "dwg"):
            raise HTTPException(status_code=400, detail="file_type must be 'dxf' or 'dwg'")

        from app.services.local_dxf_service import local_dxf_service

        logger.info("Generating DXF from image (local Potrace)...")
        dxf_path = await local_dxf_service.convert_to_dxf(request.image_url)
        if not os.path.exists(dxf_path):
            raise HTTPException(status_code=500, detail="Failed to generate DXF")

        if file_type == "dxf":
            background.add_task(_safe_unlink, dxf_path)
            return FileResponse(
                path=dxf_path,
                filename=os.path.basename(dxf_path),
                media_type="application/dxf",
                background=background,
            )

        from app.services.dwg_converter_service import dwg_converter_service

        try:
            async with _dwg_convert_lock:
                convert_result = await asyncio.to_thread(
                    dwg_converter_service.convert_dxf_path_to_dwg, dxf_path
                )
        except RuntimeError as e:
            background.add_task(_safe_unlink, dxf_path)
            raise HTTPException(status_code=503, detail=str(e))

        background.add_task(_safe_unlink, dxf_path)
        background.add_task(_safe_rmtree, convert_result.work_dir)

        return FileResponse(
            path=convert_result.dwg_path,
            filename=os.path.basename(convert_result.dwg_path),
            media_type="application/acad",
            background=background,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Design file generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/chat/generate", response_model=ChatResponse)
async def generate_chat_response(request: ChatRequest, user_data: dict = Depends(require_auth)):
    """
    Process chat message:
    1. Check Balance.
    2. Retrieve/Create Session.
    3. Load Context.
    4. Generate Response (CADLLM + Gemini).
    5. Save & Deduct.
    """
    user_id = user_data["user_id"]

    # 1. Check Request Balance
    balance_info = await subscription_service.check_request_balance(user_id)
    if not balance_info.get("can_make_request"):
        if balance_info.get("in_free_signup_tier") and balance_info.get("trial_requests", 0) == 0:
            detail = "You have used all free requests. Subscribe to a plan to continue using the workspace."
        else:
            detail = "Insufficient requests. Upgrade your plan or wait for your billing cycle to renew."
        raise HTTPException(status_code=402, detail=detail)

    try:
        session_id = request.session_id
        if not session_id:
            # Create new session
            session_id = await chat_history_service.create_session(user_id, title=request.message[:30] + "...")
        else:
            # Validate that the session exists and belongs to the user
            sessions = await chat_history_service.get_user_sessions(user_id)
            if not any(s['id'] == session_id for s in sessions):
                # Session doesn't exist or doesn't belong to user, create a new one
                logger.warning(f"Session {session_id} not found for user {user_id}, creating new session")
                session_id = await chat_history_service.create_session(user_id, title=request.message[:30] + "...")
        
        # 2. Persist User Message
        await chat_history_service.add_message(session_id, "user", request.message)

        # 3. Load Context (Optional: Fetch last N messages to pass to LLM if needed)
        # For now, we are keeping the logic similar to before, focusing on the current message + potential previous image
        
        if not cadllm_service:
             raise HTTPException(status_code=503, detail="CADLLM Service Unavailable")
        
        dxf_instruction = request.message
        
        # Use CADLLM to generate DSL Spec
        logger.info(f"Generating CADLLM response for: {dxf_instruction}")
        cad_dsl = await cadllm_service.enhance_prompt(dxf_instruction)
        
        if not cad_dsl:
            raise HTTPException(status_code=500, detail="CADLLM returned empty response")

        drawing_standard = "US_RESIDENTIAL" if request.jurisdiction == "US_IRC_BASELINE" else None

        # 4. Image Generation (Gemini) with Context
        logger.info("Generating Image with Gemini")
        
        # Try to find previous image in DB history for this session
        previous_image_url = request.previous_image_url
        if not previous_image_url:
            messages = await chat_history_service.get_session_messages(session_id)
            # Iterate backwards to find last assistant message with image
            for msg in reversed(messages):
                if msg.get("role") == "assistant" and msg.get("image_url"):
                    previous_image_url = msg.get("image_url")
                    break
        
        if previous_image_url:
            logger.info("Found previous image in history.")

        compliance_payload: Optional[Dict[str, Any]] = None
        run_compliance = (
            settings.COMPLIANCE_US_IRC_ENABLED
            and request.jurisdiction == "US_IRC_BASELINE"
            and gemini_service is not None
        )

        if run_compliance:

            async def extract_layout_safe() -> dict:
                try:
                    return await gemini_service.extract_layout_metrics_json(request.message, cad_dsl)
                except Exception as ex:
                    logger.error(f"Layout extraction failed: {ex}", exc_info=True)
                    return {}

            layout_raw, image_url = await asyncio.gather(
                extract_layout_safe(),
                gemini_service.generate_image(
                    cad_dsl,
                    original_prompt=request.message,
                    previous_image_url=previous_image_url,
                    drawing_standard=drawing_standard,
                ),
            )
            try:
                merged_raw = merge_heuristic_layout(layout_raw, request.message, cad_dsl)
                layout = parse_layout_from_llm_dict(merged_raw)
            except Exception as parse_err:
                logger.warning(f"Layout JSON did not match schema, using empty extract: {parse_err}")
                layout = LayoutExtract()
            compliance_result = validate_us_irc_baseline(layout)
            compliance_payload = compliance_result.model_dump()
        else:
            image_url = await gemini_service.generate_image(
                cad_dsl,
                original_prompt=request.message,
                previous_image_url=previous_image_url,
                drawing_standard=drawing_standard,
            )

        logger.info(f"Generated Image URL: {image_url[:50]}...")

        # 5. Persist Assistant Response
        assistant_msg = await chat_history_service.add_message(
            session_id,
            "assistant",
            cad_dsl,
            image_url=image_url,
            compliance=compliance_payload,
        )
        message_id = assistant_msg.get("id") if assistant_msg else None
        # 5b. Project persistence bridge — link a project on first successful generate.
        # Uses the real user prompt as input_text; reuses existing project on repeat generates.
        try:
            await chat_history_service.ensure_project_for_session(
                session_id=session_id,
                user_id=user_id,
                input_text=request.message,
                image_url=image_url,
                parsed_json={"cad_dsl": cad_dsl},
            )
        except Exception as bridge_err:
            # Non-fatal: generation already succeeded, don't fail the request over the bridge.
            logger.error(f"[generate] project bridge failed: {bridge_err}", exc_info=True)

        # 6. Deduct Request - ONLY AFTER SUCCESSFUL COMPLETION
        # This ensures users are not charged if any error occurred above
        # Each chat generation counts as 1 request (question + response + image)
        try:
            new_balance_info = await subscription_service.deduct_request(user_id)
        except ValueError as e:
            raise HTTPException(status_code=402, detail=str(e))
        
        # Also deduct from legacy minutes for backward compatibility
        legacy_balance = await subscription_service.deduct_minutes(user_id, 0.5)

        logger.info(f"Successfully completed request for user {user_id}. Remaining requests: {new_balance_info.get('total_requests', 0)}")

        return ChatResponse(
            session_id=session_id,
            message_id=message_id,
            original_prompt=request.message,
            ollama_response=cad_dsl,
            validated_response=cad_dsl,
            image_url=image_url,
            remaining_minutes=legacy_balance,  # Legacy field
            request_balance=new_balance_info,  # New request-based balance
            compliance=compliance_payload,
        )

    except HTTPException:
        # Re-raise HTTP exceptions without charging the user
        logger.warning(f"HTTP exception occurred for user {user_id}, no charge applied")
        raise
    except Exception as e:
        # Log error and raise without charging the user
        logger.error(f"Chat generation error for user {user_id}: {str(e)}, no charge applied", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/session")
async def create_chat_session(request: CreateSessionRequest, user_data: dict = Depends(require_auth)):
    """
    Create a new chat session.
    """
    user_id = user_data["user_id"]
    try:
        session_id = await chat_history_service.create_session(user_id, title=request.title or "New Chat")
        sessions = await chat_history_service.get_user_sessions(user_id)
        # Return the newly created session
        new_session = next((s for s in sessions if s["id"] == session_id), None)
        if new_session:
            return new_session
        return {"id": session_id, "title": request.title or "New Chat", "created_at": None, "updated_at": None}
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history")
async def get_chat_history(user_data: dict = Depends(require_auth)):
    """
    Get all chat sessions for the user.
    """
    user_id = user_data["user_id"]
    return await chat_history_service.get_user_sessions(user_id)

@router.get("/chat/history/{session_id}")
async def get_session_history(session_id: str, user_data: dict = Depends(require_auth)):
    """
    Get messages for a specific session.
    """
    # Todo: verify session belongs to user (RLS handles this in DB, but good to be safe)
    # The service blindly fetches, but RLS on Supabase side should restrict it if configured correctly.
    # We constructed the service to use the 'service_role' client (admin) which BYPASSES RLS.
    # IMPORTANT: We should verify ownership here if using admin client.
    
    user_id = user_data["user_id"]
    
    # Check ownership
    sessions = await chat_history_service.get_user_sessions(user_id)
    if not any(s['id'] == session_id for s in sessions):
        raise HTTPException(status_code=403, detail="Access denied")

    return await chat_history_service.get_session_messages(session_id)

@router.patch("/chat/history/{session_id}/title")
async def update_session_title(session_id: str, request: UpdateSessionTitleRequest, user_data: dict = Depends(require_auth)):
    """
    Update the title of a chat session.
    """
    user_id = user_data["user_id"]
    try:
        success = await chat_history_service.update_session_title(session_id, user_id, request.title)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
        return {"status": "success", "id": session_id, "title": request.title}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session title: {e}")
        raise HTTPException(status_code=500, detail="Failed to update session title")

@router.post("/chat/message/{message_id}/feedback")
async def submit_message_feedback(message_id: str, request: MessageFeedbackRequest, user_data: dict = Depends(require_auth)):
    """
    Submit thumbs up/down feedback for a generated image message. For thumbs down, optional reason can be provided.
    """
    user_id = user_data["user_id"]
    if request.reaction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="reaction must be 'up' or 'down'")
    success = await chat_history_service.upsert_feedback(
        message_id=message_id,
        user_id=user_id,
        reaction=request.reaction,
        reason=(request.reason or "").strip() or None,
    )
    if not success:
        raise HTTPException(status_code=403, detail="Message not found or access denied")
    return {"status": "success", "message_id": message_id, "reaction": request.reaction}


@router.delete("/chat/history/{session_id}")
async def delete_chat_session(session_id: str, user_data: dict = Depends(require_auth)):
    """
    Delete a chat session.
    """
    user_id = user_data["user_id"]
    try:
        success = await chat_history_service.delete_session(session_id, user_id)
        if not success:
             raise HTTPException(status_code=404, detail="Session not found or access denied")
        return {"status": "success", "id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")
