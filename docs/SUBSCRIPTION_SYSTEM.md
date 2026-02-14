# Subscription and Request Tracking System

## Overview

This document describes the subscription and request tracking system implemented for KRAFZEN AI. The system supports:

1. **Free Trial Requests**: Users get a specific number of free requests during a 14-day trial period when they subscribe to a plan
2. **Subscription Plan Requests**: Users get a monthly/annual allocation of requests based on their subscription plan
3. **Request Deduction**: Requests are automatically deducted when users generate images or DXF files

## Subscription Plans

### Plan Configuration

| Plan | Monthly Price | Annual Price | Requests/Month | Trial Requests (14 days) |
|------|--------------|--------------|----------------|-------------------------|
| Starter | $249 | $2,490 | 500 | 20 |
| Professional | $649 | $6,490 | 3,000 | 50 |
| Enterprise | $1,799 | $18,190 | 10,000 | 80 |
| Enterprise Plus | Custom | Custom | 50,000+ | 150 |

### Request Types

Each "request" counts as:

- 1 Image Generation (via Gemini)
- 1 DXF File Generation

When a user generates both an image and DXF in a single chat interaction, it counts as **1 request** (not 2).

## Database Schema

### user_subscriptions Table

```sql
CREATE TABLE user_subscriptions (
    user_id UUID PRIMARY KEY,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    
    -- Plan details
    plan_name TEXT DEFAULT 'free',
    plan_tier TEXT DEFAULT 'free',  -- Legacy field
    billing_cycle TEXT,  -- 'monthly', 'annual'
    subscription_status TEXT DEFAULT 'inactive',  -- 'inactive', 'trial', 'active', 'canceled', 'past_due'
    
    -- Free trial tracking (14 days)
    trial_start_date TIMESTAMPTZ,
    trial_end_date TIMESTAMPTZ,
    trial_requests_total INT DEFAULT 0,
    trial_requests_remaining INT DEFAULT 0,
    
    -- Subscription plan requests
    plan_requests_total INT DEFAULT 0,
    plan_requests_remaining INT DEFAULT 0,
    plan_requests_reset_date TIMESTAMPTZ,
    
    -- Legacy fields (backward compatibility)
    remaining_minutes FLOAT DEFAULT 0.0,
    total_minutes_purchased FLOAT DEFAULT 0.0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Backend API

### Subscription Service

Located in: `backend/app/services/subscription_service.py`

#### Key Methods

1. **`start_subscription(user_id, plan_name, billing_cycle, stripe_customer_id, stripe_subscription_id)`**
   - Starts a new subscription with free trial
   - Allocates trial requests based on plan
   - Sets trial period (14 days)
   - Allocates plan requests
   - Sets plan reset date

2. **`check_request_balance(user_id)`**
   - Returns current request balance
   - Returns: `{ trial_requests, plan_requests, total_requests, can_make_request, subscription_status, plan_name }`

3. **`deduct_request(user_id)`**
   - Deducts 1 request from user balance
   - Prioritizes trial requests first, then plan requests
   - Returns updated balance

4. **`reset_plan_requests(user_id)`**
   - Resets plan requests based on billing cycle
   - Called automatically when billing cycle renews
   - Sets next reset date

5. **`activate_subscription(user_id)`**
   - Activates subscription after trial or payment confirmation

### Payment Service

Located in: `backend/app/services/payment_service.py`

#### Key Methods

1. **`create_checkout_session(user_id, plan_name, billing_cycle, success_url, cancel_url)`**
   - Creates Stripe checkout session for subscription
   - Includes 14-day free trial
   - Returns checkout URL

2. **`handle_webhook(payload, sig_header)`**
   - Handles Stripe webhook events
   - Processes subscription lifecycle events:
     - `checkout.session.completed`: Start subscription with trial
     - `customer.subscription.created`: Log subscription creation
     - `customer.subscription.updated`: Update subscription status
     - `customer.subscription.deleted`: Mark as canceled
     - `invoice.payment_succeeded`: Reset plan requests for new billing cycle
     - `invoice.payment_failed`: Mark as past_due

### API Endpoints

#### POST `/api/v1/payments/create-checkout-session`

Create a Stripe checkout session for a subscription plan.

**Request Body:**

```json
{
  "plan_name": "starter",  // starter, professional, enterprise, enterprise_plus
  "billing_cycle": "monthly"  // monthly, annual
}
```

**Response:**

```json
{
  "url": "https://checkout.stripe.com/..."
}
```

#### GET `/api/v1/payments/subscription-status`

Get current subscription status and request balance.

**Response:**

```json
{
  "subscription": {
    "plan_name": "starter",
    "billing_cycle": "monthly",
    "status": "trial",
    "trial_start_date": "2026-02-09T23:00:00Z",
    "trial_end_date": "2026-02-23T23:00:00Z",
    "plan_requests_reset_date": "2026-03-25T23:00:00Z"
  },
  "balance": {
    "trial_requests": 15,
    "plan_requests": 500,
    "total_requests": 515,
    "can_make_request": true,
    "subscription_status": "trial",
    "plan_name": "starter"
  }
}
```

#### POST `/api/v1/chat/generate`

Generate chat response (image + DXF).

**Request Body:**

```json
{
  "message": "Draw a 12x10 kitchen",
  "session_id": "optional-session-id"
}
```

**Response:**

```json
{
  "session_id": "...",
  "original_prompt": "Draw a 12x10 kitchen",
  "ollama_response": "...",
  "validated_response": "...",
  "image_url": "...",
  "remaining_minutes": 99.5,  // Legacy field
  "request_balance": {
    "trial_requests": 14,
    "plan_requests": 500,
    "total_requests": 514
  }
}
```

## Frontend Integration

### Payment API

Located in: `frontend/lib/api/payment.ts`

#### Functions

1. **`createCheckoutSession(user, planName, billingCycle)`**
   - Creates checkout session
   - Returns checkout URL
   - Redirects to Stripe

2. **`getSubscriptionStatus(user)`**
   - Gets current subscription status
   - Returns balance information

### Pricing Component

Located in: `frontend/components/ui/PricingDiv.tsx`

**Features:**

- Displays plan details and pricing
- Handles "Get Started" button click
- Creates checkout session via API
- Redirects to Stripe checkout
- Shows loading state during checkout creation

## User Flow

### 1. New Subscription

1. User clicks "Get Started" on pricing page
2. Frontend calls `createCheckoutSession` API
3. Backend creates Stripe checkout session with:
   - 14-day free trial
   - Trial requests allocated
   - Plan requests allocated
4. User redirected to Stripe checkout
5. User enters payment details
6. Stripe webhook `checkout.session.completed` triggers
7. Backend calls `start_subscription`:
   - Sets trial period (14 days)
   - Allocates trial requests (e.g., 20 for Starter)
   - Allocates plan requests (e.g., 500 for Starter)
   - Sets plan reset date (30 days after trial ends for monthly)
   - Sets status to "trial"

### 2. Making Requests During Trial

1. User generates image/DXF
2. Backend checks balance via `check_request_balance`
3. If `can_make_request` is true:
   - Process request
   - Call `deduct_request`
   - Deduct from trial_requests first
   - If trial_requests = 0, deduct from plan_requests
4. Return updated balance to frontend

### 3. Trial Expiration

1. After 14 days, trial expires
2. On next request, `_check_trial_expiry` runs
3. Status updated from "trial" to "active"
4. User continues using plan_requests

### 4. Billing Cycle Renewal

1. Stripe charges customer for new billing cycle
2. Webhook `invoice.payment_succeeded` triggers
3. Backend calls `reset_plan_requests`:
   - Resets plan_requests_remaining to plan_requests_total
   - Sets new plan_requests_reset_date (30 days for monthly, 365 for annual)

### 5. Payment Failure

1. Stripe fails to charge customer
2. Webhook `invoice.payment_failed` triggers
3. Backend updates status to "past_due"
4. User cannot make new requests until payment succeeds

### 6. Subscription Cancellation

1. User cancels subscription in Stripe
2. Webhook `customer.subscription.deleted` triggers
3. Backend updates status to "canceled"
4. User can continue using remaining requests until they run out

## Request Deduction Logic

```python
# Priority: Trial requests first, then plan requests
if trial_requests_remaining > 0:
    trial_requests_remaining -= 1
else:
    plan_requests_remaining -= 1
```

## Migration

To apply the database changes:

```bash
# Run migration
psql $SUPABASE_DATABASE_URL -f supabase/migrations/20260209_add_subscription_requests.sql
```

Or use Supabase CLI:

```bash
supabase db push
```

## Environment Variables

Add to `.env`:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Frontend
NEXT_PUBLIC_CALENDLY_URL=https://calendly.com/your-calendar-link
```

## Testing

### Test Subscription Flow

1. **Create Checkout Session:**

```bash
curl -X POST http://localhost:8000/api/v1/payments/create-checkout-session \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_name": "starter",
    "billing_cycle": "monthly"
  }'
```

1. **Check Subscription Status:**

```bash
curl -X GET http://localhost:8000/api/v1/payments/subscription-status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

1. **Test Request Deduction:**

```bash
curl -X POST http://localhost:8000/api/v1/chat/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Draw a 12x10 kitchen"
  }'
```

### Test Stripe Webhooks Locally

Use Stripe CLI:

```bash
stripe listen --forward-to localhost:8000/api/v1/payments/webhook
stripe trigger checkout.session.completed
stripe trigger invoice.payment_succeeded
```

## Backward Compatibility

The system maintains backward compatibility with the legacy "minutes" system:

- `remaining_minutes` field still exists
- `deduct_minutes()` and `add_minutes()` methods still work
- Old API endpoints continue to function

This allows for gradual migration from minutes to requests.

## Future Enhancements

1. **Usage Analytics**: Track request usage over time
2. **Overage Charges**: Allow users to purchase additional requests
3. **Plan Upgrades**: Allow users to upgrade/downgrade plans
4. **Team Management**: Share requests across team members
5. **Request Rollover**: Allow unused requests to roll over to next billing cycle (optional)
