# Request Charging Logic

## 📋 Overview

This document explains how requests are charged in the KRAFZEN AI system to ensure fair billing for users.

## ✅ Charging Rules

### **Rule 1: One Request = One Complete Interaction**

A single request consists of:

1. **User Question** (e.g., "Create a cube")
2. **AI Processing** (CADLLM generates CAD DSL)
3. **Image Generation** (Gemini creates visualization)
4. **Response Delivery** (User receives answer + image)

**Total Charge: 1 Request** ✅

### **Rule 2: No Charge on Errors**

Users are **NOT charged** if:

- ❌ CADLLM service is unavailable
- ❌ CADLLM returns empty response
- ❌ Gemini image generation fails
- ❌ Database persistence fails
- ❌ Any other error occurs during processing

**Charge only on successful completion** ✅

## 🔄 Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User sends question                                      │
│    "Create a 10x10x10 cube"                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Check Request Balance                                    │
│    - Trial requests + Plan requests > 0?                    │
│    - If NO → Return 402 error (no charge)                   │
│    - If YES → Continue                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Process Request (TRY BLOCK)                              │
│    a. Create/validate session                               │
│    b. Save user message to DB                               │
│    c. Generate CAD DSL with CADLLM                          │
│    d. Generate image with Gemini                            │
│    e. Save assistant response to DB                         │
│                                                             │
│    ⚠️  If ANY error occurs here → STOP, NO CHARGE          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Deduct Request (ONLY IF STEP 3 SUCCEEDS)                │
│    - Deduct 1 from trial_requests (if available)           │
│    - OR deduct 1 from plan_requests                         │
│    - Log successful completion                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Return Response                                          │
│    - Session ID                                             │
│    - Original prompt                                        │
│    - CAD DSL response                                       │
│    - Image URL                                              │
│    - Updated request balance                                │
└─────────────────────────────────────────────────────────────┘
```

## 💡 Examples

### Example 1: Successful Request

```
User: "Create a sphere with radius 5"
↓
System: Checks balance (50 requests available) ✅
↓
System: Generates CAD DSL ✅
↓
System: Generates image ✅
↓
System: Saves to database ✅
↓
System: Deducts 1 request (49 remaining) ✅
↓
User: Receives response + image ✅

CHARGED: 1 request
```

### Example 2: CADLLM Error (No Charge)

```
User: "Create a complex shape"
↓
System: Checks balance (50 requests available) ✅
↓
System: CADLLM service unavailable ❌
↓
System: Raises HTTPException ❌
↓
System: NO DEDUCTION (50 requests still available) ✅
↓
User: Receives error message ❌

CHARGED: 0 requests
```

### Example 3: Gemini Error (No Charge)

```
User: "Create a cube"
↓
System: Checks balance (50 requests available) ✅
↓
System: Generates CAD DSL ✅
↓
System: Gemini image generation fails ❌
↓
System: Raises Exception ❌
↓
System: NO DEDUCTION (50 requests still available) ✅
↓
User: Receives error message ❌

CHARGED: 0 requests
```

### Example 4: Insufficient Balance (No Charge)

```
User: "Create a cylinder"
↓
System: Checks balance (0 requests available) ❌
↓
System: Returns 402 error immediately ❌
↓
System: NO PROCESSING, NO DEDUCTION ✅
↓
User: Receives "Insufficient requests" error ❌

CHARGED: 0 requests
```

## 🔍 Code Implementation

### Location: `/backend/app/routes/chat_routes.py`

```python
@router.post("/chat/generate")
async def chat_generate(request: ChatRequest, user_data: dict = Depends(require_auth)):
    user_id = user_data["user_id"]

    # 1. Check Request Balance BEFORE processing
    balance_info = await subscription_service.check_request_balance(user_id)
    if not balance_info.get("can_make_request"):
        raise HTTPException(
            status_code=402, 
            detail="Insufficient requests. Please upgrade your plan."
        )

    try:
        # 2. Process request (CADLLM + Gemini + DB)
        session_id = ...
        cad_dsl = await cadllm_service.enhance_prompt(...)
        image_url = await gemini_service.generate_image(...)
        await chat_history_service.add_message(...)

        # 3. Deduct ONLY after successful completion
        new_balance_info = await subscription_service.deduct_request(user_id)
        
        logger.info(f"Successfully completed request. Remaining: {new_balance_info['total_requests']}")

        return ChatResponse(...)

    except HTTPException:
        # Re-raise HTTP exceptions WITHOUT charging
        logger.warning(f"HTTP exception, no charge applied")
        raise
    except Exception as e:
        # Log error and raise WITHOUT charging
        logger.error(f"Error: {str(e)}, no charge applied")
        raise HTTPException(status_code=500, detail=str(e))
```

## 📊 Request Deduction Logic

### From `subscription_service.py`

```python
async def deduct_request(self, user_id: str) -> Dict[str, Any]:
    """
    Deduct ONE request from user balance.
    Deducts from trial requests first, then plan requests.
    """
    # Get current balance
    trial_requests = current_sub.get("trial_requests_remaining", 0)
    plan_requests = current_sub.get("plan_requests_remaining", 0)
    
    # Deduct from trial first
    if trial_requests > 0:
        new_trial_requests = trial_requests - 1  # ← Deduct 1
        # Update database
        return {
            "trial_requests": new_trial_requests,
            "plan_requests": plan_requests,
            "total_requests": new_trial_requests + plan_requests
        }
    else:
        # Deduct from plan
        new_plan_requests = plan_requests - 1  # ← Deduct 1
        # Update database
        return {
            "trial_requests": 0,
            "plan_requests": new_plan_requests,
            "total_requests": new_plan_requests
        }
```

## ⚠️ Important Notes

1. **Pre-flight Check**: Balance is checked BEFORE any processing
2. **Atomic Deduction**: Request is deducted AFTER all processing succeeds
3. **Error Safety**: Any error prevents deduction
4. **Trial Priority**: Trial requests are always used before plan requests
5. **Logging**: All deductions and errors are logged for audit

## 🎯 User Experience

### Good Experience ✅

- User sends question
- Gets response + image
- Sees updated balance (49 requests remaining)
- Knows exactly what they paid for

### Protected Experience ✅

- User sends question
- System error occurs
- User NOT charged
- Balance unchanged (50 requests remaining)
- User can retry without penalty

## 📈 Monitoring

### Logs to Watch

**Successful Request:**

```
INFO: Successfully completed request for user abc123. Remaining requests: 49
```

**Error (No Charge):**

```
WARNING: HTTP exception occurred for user abc123, no charge applied
ERROR: Chat generation error for user abc123: CADLLM unavailable, no charge applied
```

**Insufficient Balance:**

```
WARNING: User abc123 attempted request with 0 balance
```

## 🔐 Security

- Balance check happens server-side (cannot be bypassed)
- Deduction is atomic (database transaction)
- All actions are logged with user_id
- Errors are caught and logged for debugging

## ✅ Summary

**Fair Charging Principles:**

1. ✅ **1 Request = 1 Complete Interaction** (question + answer + image)
2. ✅ **No Charge on Errors** (system failures don't cost users)
3. ✅ **Pre-flight Validation** (check balance before processing)
4. ✅ **Post-success Deduction** (charge only after completion)
5. ✅ **Transparent Logging** (all actions auditable)

Users can trust that they only pay for successful, complete responses! 🎉
