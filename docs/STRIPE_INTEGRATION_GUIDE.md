# Stripe Integration Guide - Simplified Approach

## ✅ Current Setup

You have Stripe Buy Buttons already configured! The pricing page now redirects directly to your Stripe checkout pages.

## 🎯 Do You Need Stripe Secret Keys?

**Short Answer: YES, but only for webhook handling and request tracking.**

### What Works WITHOUT Secret Keys

- ✅ Users can click "Get Started" and go to Stripe checkout
- ✅ Users can complete payment
- ✅ Stripe will handle the subscription

### What DOESN'T Work Without Secret Keys

- ❌ Automatic request tracking (trial requests, plan requests)
- ❌ Webhook verification (knowing when payments succeed)
- ❌ Subscription status updates in your database
- ❌ Request deduction when users generate images/DXF

## 📋 What You Need to Add

### 1. Add Stripe Keys to `.env`

Add these lines to your `/Users/kiruthika/Projects/KRAFZEN-AI-/.env` file:

```bash
# ============================================================================
# Stripe Configuration
# ============================================================================
STRIPE_PUBLISHABLE_KEY=pk_live_51S1SILEnqjyMP8C8mdd9dSNfddIPvSgDPDdAvc8OxrUViJlmg4vUemnGlh7lqF2ecmNFecAjMjrqmgCazKzNPEFI00u1JzkxgH
STRIPE_SECRET_KEY=sk_live_...  # Get this from Stripe Dashboard -> Developers -> API Keys
STRIPE_WEBHOOK_SECRET=whsec_...  # Get this after setting up webhook endpoint (see step 2)
```

### 2. Set Up Stripe Webhook

#### A. Get Your Webhook Endpoint URL

Your webhook endpoint will be: `https://your-production-domain.com/api/v1/payments/webhook`

For local testing: `http://localhost:8000/api/v1/payments/webhook`

#### B. Configure in Stripe Dashboard

1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to **Developers** → **Webhooks**
3. Click **Add endpoint**
4. Enter your webhook URL
5. Select these events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
6. Click **Add endpoint**
7. Copy the **Signing secret** (starts with `whsec_...`)
8. Add it to your `.env` as `STRIPE_WEBHOOK_SECRET`

### 3. Link Stripe Products to Your Plans

You need to get the Stripe Price IDs from your buy buttons. Here's how:

#### A. Extract Price IDs from Stripe Dashboard

1. Go to [Stripe Dashboard](https://dashboard.stripe.com) → **Products**
2. Find each product (Starter, Professional, Enterprise)
3. Click on the product
4. Copy the **Price ID** (starts with `price_...`)

#### B. Update the Subscription Service

Once you have the Price IDs, update `/Users/kiruthika/Projects/KRAFZEN-AI-/backend/app/services/subscription_service.py`:

```python
# Add this mapping at the top of the file
STRIPE_PRICE_IDS = {
    "starter": {
        "monthly": "price_xxxxx",  # From $249/month buy button
        "annual": "price_xxxxx",   # From $2,490/year buy button
    },
    "professional": {
        "monthly": "price_xxxxx",  # From $649/month buy button
        "annual": "price_xxxxx",   # From $6,490/year buy button
    },
    "enterprise": {
        "monthly": "price_xxxxx",  # From $1,799/month buy button
        "annual": "price_xxxxx",   # From $18,190/year buy button
    },
    "enterprise_plus": {
        "monthly": None,  # Custom pricing
        "annual": None,   # Custom pricing
    }
}
```

## 🔄 How It Works Now

### User Flow

1. User clicks "Get Started" on pricing page
2. Redirected to Stripe checkout (your buy button link)
3. User completes payment on Stripe
4. Stripe sends webhook to your backend
5. Backend receives webhook and:
   - Verifies it's from Stripe (using webhook secret)
   - Creates/updates subscription in database
   - Allocates trial requests (14 days)
   - Allocates plan requests
6. User can now use the platform with their request allocation

### Request Tracking

- When user generates image/DXF, backend calls `subscription_service.deduct_request()`
- Deducts from trial requests first, then plan requests
- Requests reset monthly/annually based on billing cycle

## 🧪 Testing Locally

### 1. Install Stripe CLI

```bash
brew install stripe/stripe-cli/stripe
```

### 2. Login to Stripe

```bash
stripe login
```

### 3. Forward Webhooks to Local Server

```bash
stripe listen --forward-to localhost:8000/api/v1/payments/webhook
```

This will give you a webhook secret starting with `whsec_...`. Use this for local testing.

### 4. Trigger Test Events

```bash
# Test subscription created
stripe trigger checkout.session.completed

# Test payment succeeded
stripe trigger invoice.payment_succeeded
```

## 📊 Current Implementation Status

✅ **Completed:**

- Database schema with request tracking
- Subscription service with trial and plan requests
- Payment service with webhook handlers
- Frontend pricing page with Stripe buy button links
- Request deduction in chat routes

⚠️ **Needs Configuration:**

- Stripe Secret Key (from dashboard)
- Stripe Webhook Secret (after webhook setup)
- Stripe Price IDs mapping (optional, for programmatic checkout)

## 🚀 Quick Start (Minimum Required)

To get basic functionality working:

1. **Add Stripe Secret Key to `.env`:**

   ```bash
   STRIPE_SECRET_KEY=sk_live_...
   ```

2. **Set up webhook endpoint** in Stripe Dashboard

3. **Add Webhook Secret to `.env`:**

   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

4. **Restart your backend server**

That's it! The system will now:

- Track subscriptions via webhooks
- Allocate trial and plan requests
- Deduct requests as users generate content
- Reset requests on billing cycle renewal

## 🎯 Summary

**You DON'T need secret keys for:**

- Users to checkout and pay (buy buttons handle this)

**You DO need secret keys for:**

- Webhook verification
- Automatic request tracking
- Subscription management in your database
- Request deduction and reset

The current implementation uses your existing Stripe Buy Buttons for checkout, which is simpler and works great! The secret keys are only needed for the backend to track and manage subscriptions automatically.
