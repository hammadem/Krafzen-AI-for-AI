import asyncio
import json
import logging
import os
import shutil
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from app.db.queries.project_queries import get_project
from fastapi.responses import FileResponse, StreamingResponse
from httpx import HTTPError
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field
from uuid import UUID
from fastapi.concurrency import run_in_threadpool
from app.services.reference_retrieval import retrieve_reference, format_reference_answer, reference_register

from app.compliance.extraction_fallback import merge_heuristic_layout
from app.compliance.models import LayoutExtract
from app.compliance.validator import (
    parse_layout_from_llm_dict,
    validate_us_irc_baseline,
)
from app.core.config import settings
from app.middlewares.auth import require_auth
from app.models.chat_model import (
    ChatRequest,
    ChatResponse,
    CreateSessionRequest,
    DesignFileRequest,
    DxfRequest,
    MessageFeedbackRequest,
    UpdateSessionTitleRequest,
)
from app.services.activity_service import record_audit_event
from app.services.cadllm_service import cadllm_service
from app.services.chat_history_service import chat_history_service
from app.services.gemini_service import gemini_service
from app.services.subscription_service import subscription_service

router = APIRouter()
logger = logging.getLogger(__name__)

# One DWG conversion at a time per worker (ODA+Xvfb is heavy; parallel runs cause timeouts).
_dwg_convert_lock = asyncio.Lock()


class SuggestionDecisionRequest(BaseModel):
    decision: Literal["accepted", "rejected"]


@router.post("/chat/dxf")
async def generate_dxf(request: DxfRequest, user_data: dict = Depends(require_auth)):
    """
    Generates a DXF file from an image URL.
    Uses External Service (Api2Convert) for high-fidelity Raster-to-Vector conversion.
    """
    try:
        # Validate auth
        user_data["user_id"]
        
        from app.services.local_dxf_service import local_dxf_service, validate_image_source
        try:
            validate_image_source(request.image_url)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
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

    except HTTPException:
        raise
    except Exception:
        logger.exception("DXF Generation Error")
        raise HTTPException(status_code=500, detail="DXF generation failed")


def _safe_unlink(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.unlink(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        logger.warning("Unable to remove temporary file %s: %s", path, exc)


def _safe_rmtree(path: str) -> None:
    if not path or not os.path.exists(path):
        return
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        logger.warning("Unable to remove temporary directory %s: %s", path, exc)


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

        from app.services.local_dxf_service import local_dxf_service, validate_image_source
        try:
            validate_image_source(request.image_url)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

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
        logger.exception("Design file generation error")
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

    session_id = request.session_id
    session_project_id: str | None = None
    generation_id: str | None = None
    generation_started = False
    generation_completed = False
    generation_stage = "session_setup"

    try:
        if not session_id:
            # Create new session
            session_id = await chat_history_service.create_session(user_id, title=request.message[:30] + "...")
        else:
            # Validate that the session exists and belongs to the user
            sessions = await chat_history_service.get_user_sessions(user_id)
            session_record = next((s for s in sessions if s["id"] == session_id), None)
            if not session_record:
                # Never silently reuse or replace a client-supplied foreign session.
                raise HTTPException(status_code=404, detail="Chat session not found")
            else:
                session_project_id = session_record.get("project_id")
        
        if session_project_id:
            linked_project = await get_project(session_project_id, user_data)
            if not linked_project or linked_project.get("archived_at"):
                raise HTTPException(status_code=409, detail="Restore the linked project before generating a design")

        # 2. Persist User Message
        await chat_history_service.add_message(session_id, "user", request.message)

        # Make the project reference available before AI work starts so the full
        # lifecycle can be retrieved from project activity. The prompt remains
        # in the existing project/chat storage, never in audit metadata.
        try:
            session_project_id = await chat_history_service.ensure_project_for_session(
                session_id=session_id,
                user_id=user_id,
                input_text=request.message,
            ) or session_project_id
        except Exception:
            logger.exception("[generate] project bridge failed")

        generation_id = str(uuid4())
        generation_stage = "generation_started_audit"
        generation_started = True
        await record_audit_event(
            action="ai.generation_started",
            entity_type="ai_generation",
            entity_id=generation_id,
            actor_user_id=user_id,
            project_id=session_project_id,
            metadata={
                "generation_id": generation_id,
                "session_id": session_id,
                "jurisdiction": request.jurisdiction,
            },
        )

        # 3. Load Context (Optional: Fetch last N messages to pass to LLM if needed)
        # For now, we are keeping the logic similar to before, focusing on the current message + potential previous image
        
        generation_stage = "prompt_enhancement"
        if not cadllm_service:
             raise HTTPException(status_code=503, detail="CADLLM Service Unavailable")
        
        dxf_instruction = request.message
        
        # Use CADLLM to generate DSL Spec
        logger.info("Generating CADLLM response")
        cad_dsl = await cadllm_service.enhance_prompt(dxf_instruction)
        
        if not cad_dsl:
            raise HTTPException(status_code=500, detail="CADLLM returned empty response")

        drawing_standard = "US_RESIDENTIAL" if request.jurisdiction == "US_IRC_BASELINE" else None

        # 4. Image Generation (Gemini) with Context
        logger.info("Generating Image with Gemini")
        
        # Try to find previous image in DB history for this session
        previous_image_url = request.previous_image_url
        if not previous_image_url:
            history_res = await chat_history_service.get_session_messages(session_id, limit=20)
            messages = history_res.get("messages", []) if isinstance(history_res, dict) else history_res
            # Iterate backwards to find last assistant message with image
            for msg in reversed(messages):
                if msg.get("role") == "assistant" and msg.get("image_url"):
                    previous_image_url = msg.get("image_url")
                    break
        
        if previous_image_url:
            logger.info("Found previous image in history.")

        compliance_payload: dict[str, Any] | None = None
        run_compliance = (
            settings.COMPLIANCE_US_IRC_ENABLED
            and request.jurisdiction == "US_IRC_BASELINE"
            and gemini_service is not None
        )

        if run_compliance:
            review_id = str(uuid4())
            await record_audit_event(
                action="ai.review_started",
                entity_type="ai_review",
                entity_id=review_id,
                actor_user_id=user_id,
                project_id=session_project_id,
                metadata={
                    "review_id": review_id,
                    "generation_id": generation_id,
                    "session_id": session_id,
                    "jurisdiction": request.jurisdiction,
                },
            )

            async def extract_layout_safe() -> dict:
                try:
                    return await gemini_service.extract_layout_metrics_json(request.message, cad_dsl)
                except Exception:
                    logger.exception("Layout extraction failed")
                    return {}

            generation_stage = "compliance_review"
            layout_raw, image_result = await asyncio.gather(
                extract_layout_safe(),
                gemini_service.generate_image(
                    cad_dsl,
                    original_prompt=request.message,
                    previous_image_url=previous_image_url,
                    drawing_standard=drawing_standard,
                ),
                return_exceptions=True,
            )
            if isinstance(layout_raw, BaseException):
                raise layout_raw

            try:
                merged_raw = merge_heuristic_layout(layout_raw, request.message, cad_dsl)
                layout = parse_layout_from_llm_dict(merged_raw)
            except (KeyError, TypeError, ValueError) as parse_err:
                logger.warning(f"Layout JSON did not match schema, using empty extract: {parse_err}")
                layout = LayoutExtract()

            try:
                compliance_result = validate_us_irc_baseline(layout)
                compliance_payload = compliance_result.model_dump()
            except Exception as review_error:
                await record_audit_event(
                    action="ai.review_failed",
                    entity_type="ai_review",
                    entity_id=review_id,
                    actor_user_id=user_id,
                    project_id=session_project_id,
                    metadata={
                        "review_id": review_id,
                        "generation_id": generation_id,
                        "session_id": session_id,
                        "error_type": type(review_error).__name__,
                    },
                )
                raise
            else:
                await record_audit_event(
                    action="ai.review_completed",
                    entity_type="ai_review",
                    entity_id=review_id,
                    actor_user_id=user_id,
                    project_id=session_project_id,
                    metadata={
                        "review_id": review_id,
                        "generation_id": generation_id,
                        "session_id": session_id,
                        "jurisdiction": request.jurisdiction,
                    },
                )

            if isinstance(image_result, Exception):
                raise image_result
            image_url = image_result
        else:
            generation_stage = "image_generation"
            if gemini_service is None:
                raise HTTPException(status_code=503, detail="Image generation provider unavailable")
            image_url = await gemini_service.generate_image(
                cad_dsl,
                original_prompt=request.message,
                previous_image_url=previous_image_url,
                drawing_standard=drawing_standard,
            )

        if not isinstance(image_url, str) or not image_url.strip() or image_url.startswith("https://placehold.co/"):
            raise HTTPException(
                status_code=502,
                detail="Image generation failed. Check the backend logs and Gemini configuration.",
            )

        logger.info("Generated image for chat response")

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
            session_project_id = await chat_history_service.ensure_project_for_session(
                session_id=session_id,
                user_id=user_id,
                input_text=request.message,
                image_url=image_url,
            ) or session_project_id
        except Exception:
            # Non-fatal: generation already succeeded, don't fail the request over the bridge.
            logger.exception("[generate] project bridge failed")

        generation_stage = "audit_completion"
        generation_completed = True
        await record_audit_event(
            action="ai.generation_completed",
            entity_type="ai_generation",
            entity_id=generation_id,
            actor_user_id=user_id,
            project_id=session_project_id,
            metadata={
                "generation_id": generation_id,
                "session_id": session_id,
                "assistant_message_id": message_id,
            },
        )

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
        if generation_started and generation_id and session_id and not generation_completed:
            await _record_generation_failure(
                generation_id, session_id, user_id, session_project_id,
                generation_stage, "HTTPException"
            )
        raise
    except (APIError, HTTPError, KeyError, RuntimeError, TypeError, ValueError) as e:
        # Log error and raise without charging the user
        logger.exception("Chat generation error for user %s; no charge applied", user_id)
        if generation_started and generation_id and session_id and not generation_completed:
            await _record_generation_failure(
                generation_id, session_id, user_id, session_project_id,
                generation_stage, type(e).__name__
            )
        raise HTTPException(status_code=500, detail=str(e))

async def _record_generation_failure(
    generation_id: str,
    session_id: str,
    user_id: str,
    project_id: str | None,
    stage: str,
    error_type: str,
) -> None:
    try:
        await record_audit_event(
            action="ai.generation_failed",
            entity_type="ai_generation",
            entity_id=generation_id,
            actor_user_id=user_id,
            project_id=project_id,
            metadata={
                "generation_id": generation_id,
                "session_id": session_id,
                "stage": stage,
                "error_type": error_type,
            },
        )
    except Exception as audit_error:
        logger.exception(
            "Generation failed and its audit event could not be recorded "
            "(generation_id=%s, error_type=%s)",
            generation_id,
            type(audit_error).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Generation failed and its audit event could not be recorded",
        ) from audit_error

@router.post("/chat/generate/stream")
async def generate_chat_response_stream(request: ChatRequest, user_data: dict = Depends(require_auth)):
    """SSE delivery of the same verified, persisted generation as /chat/generate.

    Providers currently return complete output, not a token stream. Emit a
    progress event while the shared pipeline runs; only deliver generated
    content after it has passed validation, persistence and request deduction.
    """
    user_id = user_data["user_id"]
    balance_info = await subscription_service.check_request_balance(user_id)
    if not balance_info.get("can_make_request"):
        raise HTTPException(status_code=402, detail="Insufficient requests.")
    if request.session_id:
        sessions = await chat_history_service.get_user_sessions(user_id)
        if not any(str(row.get("id")) == request.session_id for row in sessions):
            raise HTTPException(status_code=404, detail="Chat session not found")

    def event(data):
        return "data: " + json.dumps(data, ensure_ascii=False, allow_nan=False) + "\n\n"

    async def sse_generator():
        yield event({"type": "progress", "stage": "generating"})
        try:
            result = await generate_chat_response(request, user_data)
            payload = result.model_dump(mode="json")
            yield event({"type": "init", "session_id": payload["session_id"]})
            if payload.get("validated_response"):
                yield event({"type": "token", "token": payload["validated_response"]})
            yield event({**payload, "type": "complete"})
        except HTTPException as exc:
            logger.warning("Shared chat generation failed with HTTP %s", exc.status_code)
            yield event({"type": "error", "error": "Generation could not complete. Check access, available requests, and AI configuration.", "status": exc.status_code})
        except Exception:
            logger.exception("Streaming generation failed")
            yield event({"type": "error", "error": "Generation failed."})

    return StreamingResponse(sse_generator(), media_type="text/event-stream", headers={
        "Cache-Control": "no-store", "X-Accel-Buffering": "no",
    })


class ReferenceRequest(BaseModel):
    session_id: UUID
    question: str = Field(min_length=1, max_length=500)


@router.get("/chat/reference-register")
async def get_reference_register(user_data: dict = Depends(require_auth)):
    try:
        return await run_in_threadpool(reference_register)
    except (ValueError, OSError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail="Approved reference index unavailable") from exc


@router.post("/chat/reference")
async def answer_reference_question(request: ReferenceRequest, user_data: dict = Depends(require_auth)):
    """Retrieve approved sources locally; no external inference or customer indexing."""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Enter a technical reference question")
    session_id = str(request.session_id)
    try:
        sessions = await chat_history_service.get_user_sessions(user_data["user_id"])
        session = next((s for s in sessions if str(s["id"]) == session_id), None)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        if session.get("project_id"):
            project = await get_project(session["project_id"], user_data)
            if not project or project.get("archived_at"):
                raise HTTPException(status_code=409, detail="Restore project before writing chat messages")
        hits = await run_in_threadpool(retrieve_reference, question)
        answer = format_reference_answer(hits)
        user_message = await chat_history_service.add_message(session_id, "user", "/reference " + question)
        if not user_message.get("id"):
            raise RuntimeError("Reference question was not saved")
        assistant = await chat_history_service.add_message(session_id, "assistant", answer)
        if not assistant.get("id"):
            raise RuntimeError("Reference response was not saved")
        return {"session_id":session_id, "message_id":assistant["id"], "original_prompt":question,
                "ollama_response":"", "validated_response":answer, "image_url":"",
                "references":hits, "mode":"local_approved_reference_retrieval"}
    except HTTPException:
        raise
    except (APIError, HTTPError, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
        logger.exception("Reference retrieval unavailable")
        raise HTTPException(status_code=503, detail="Approved reference retrieval or persistence unavailable") from exc


@router.post("/chat/session")
async def create_chat_session(request: CreateSessionRequest, user_data: dict = Depends(require_auth)):
    """
    Create a new chat session.
    """
    user_id = user_data["user_id"]
    try:
        project_id = str(request.project_id) if request.project_id else None
        if project_id:
            project = await get_project(project_id, user_data)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            if project.get("archived_at"):
                raise HTTPException(status_code=409, detail="Restore project before editing")
            sessions = await chat_history_service.get_user_sessions(user_id)
            existing = next((s for s in sessions if s.get("project_id") == project_id), None)
            if existing:
                return existing
            session_id = await chat_history_service.create_session(user_id, title=(project.get("title") or project.get("input_text") or "Project")[:200], project_id=project_id)
        else:
            session_id = await chat_history_service.create_session(user_id, title=request.title or "New Chat")
        sessions = await chat_history_service.get_user_sessions(user_id)
        # Return the newly created session
        new_session = next((s for s in sessions if s["id"] == session_id), None)
        if new_session:
            return new_session
        raise RuntimeError("Created chat session could not be read")
    except HTTPException:
        raise
    except (APIError, HTTPError, KeyError, RuntimeError, TypeError, ValueError):
        logger.exception("Error creating session")
        raise HTTPException(status_code=503, detail="Chat session unavailable")

@router.get("/chat/history")
async def get_chat_history(user_data: dict = Depends(require_auth)):
    """
    Get all chat sessions for the user.
    """
    user_id = user_data["user_id"]
    try:
        return await chat_history_service.get_user_sessions(user_id)
    except (APIError, HTTPError, RuntimeError, TypeError, ValueError):
        raise HTTPException(status_code=503, detail="Chat history unavailable")

@router.get("/chat/history/{session_id}")
async def get_session_history(
    session_id: str,
    response: Response,
    limit: int = Query(30, ge=1, le=100),
    before: str | None = Query(None, max_length=100),
    user_data: dict = Depends(require_auth)
):
    """
    Get paginated messages for a specific session with timing instrumentation headers.
    """
    import time
    t_start = time.perf_counter()
    user_id = user_data["user_id"]
    t_auth = time.perf_counter()

    # Check ownership
    sessions = await chat_history_service.get_user_sessions(user_id)
    t_sessions = time.perf_counter()
    if not any(s['id'] == session_id for s in sessions):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        result = await chat_history_service.get_session_messages(session_id, limit=limit, before=before)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Chat messages unavailable")

    t_end = time.perf_counter()
    auth_ms = round((t_auth - t_start) * 1000, 2)
    session_check_ms = round((t_sessions - t_auth) * 1000, 2)
    total_ms = round((t_end - t_start) * 1000, 2)

    db_ms = result.get("metrics", {}).get("db_query_ms", 0)
    fb_ms = result.get("metrics", {}).get("feedback_query_ms", 0)

    # Set Server-Timing header for browser DevTools performance profiling
    response.headers["Server-Timing"] = (
        f"auth;dur={auth_ms}, session;dur={session_check_ms}, db;dur={db_ms}, fb;dur={fb_ms}, total;dur={total_ms}"
    )

    logger.info(
        f"[PERF] GET /chat/history/{session_id}: total={total_ms}ms, auth={auth_ms}ms, "
        f"session_check={session_check_ms}ms, db={db_ms}ms, fb={fb_ms}ms, "
        f"msgs={len(result.get('messages', []))}, has_more={result.get('has_more')}"
    )

    return result

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
    except (APIError, HTTPError, KeyError, RuntimeError, TypeError, ValueError):
        logger.exception("Error updating session title")
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


@router.post("/chat/message/{message_id}/suggestion-decision")
async def record_suggestion_decision(
    message_id: str,
    request: SuggestionDecisionRequest,
    user_data: dict = Depends(require_auth),
):
    user_id = user_data["user_id"]
    context = await chat_history_service.get_assistant_message_context(message_id, user_id)
    if not context:
        raise HTTPException(status_code=404, detail="Assistant suggestion not found")

    await record_audit_event(
        action=f"ai.suggestion_{request.decision}",
        entity_type="ai_suggestion",
        entity_id=message_id,
        actor_user_id=user_id,
        project_id=context.get("project_id"),
        metadata={
            "suggestion_id": message_id,
            "message_id": message_id,
            "session_id": context["session_id"],
            "decision": request.decision,
        },
    )
    return {"status": "success", "suggestion_id": message_id, "decision": request.decision}


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
    except (APIError, HTTPError, KeyError, RuntimeError, TypeError, ValueError):
        logger.exception("Delete error")
        raise HTTPException(status_code=500, detail="Failed to delete session")
