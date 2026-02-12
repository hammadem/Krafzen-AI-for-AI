# ✅ Stripe & Calendly Integration (Iframe Approach)

## 🎉 What's Implemented

This integration wraps your **existing Stripe checkout links** and **Calendly booking link** in premium glassmorphic modals that match your app's design.

### ✨ Features

- **No API keys required** - Uses your existing links
- **Premium glassmorphic design** - Matches your app aesthetic
- **Smooth animations** - Loading states and transitions
- **Mobile responsive** - Works on all devices
- **Easy to use** - Click and book/pay

## 📁 Components Created

### 1. **StripeCheckoutModal** (`frontend/components/StripePaymentModal.tsx`)

- Wraps Stripe checkout links in a glassmorphic iframe
- Shows loading state while iframe loads
- "Open in new tab" option for users who prefer it
- Integrated into pricing page "Get Started" buttons

### 2. **CalendlyBooking** (`frontend/components/CalendlyBooking.tsx`)

- Wraps Calendly booking link in a glassmorphic iframe
- Premium design with smooth loading animation
- Integrated into "Book a Demo" button on home page

## 🎯 How It Works

### Stripe Payments

1. User clicks "Get Started" on any pricing plan
2. Modal opens with your existing Stripe checkout link embedded
3. User completes payment in the iframe
4. Stripe handles everything (no backend code needed)

### Calendly Booking

1. User clicks "Book a Demo" button
2. Modal opens with your Calendly scheduler embedded
3. User selects time and books demo
4. Calendly handles everything (no backend code needed)

## 🎨 Design Features

### Glassmorphic Modal

- Black background with 95% opacity
- Backdrop blur effects
- Gradient overlays (green for payments, blue/purple for bookings)
- Smooth border animations
- Loading states with spinners

### Color Scheme

- **Primary**: Green (#4ade80) accents
- **Background**: Black with transparency
- **Text**: White with gray variations
- **Borders**: White with 10% opacity

## 🔐 Stripe Environments (Test vs Live)

- **Local, Vercel Preview, Vercel Development:** Use **test** keys (`pk_test_...`, `sk_test_...`). The app uses embedded Stripe checkout in test mode; use [Stripe test cards](https://docs.stripe.com/testing) (e.g. **4242 4242 4242 4242**, any future expiry, any CVC). The payment modal shows a “Test mode” hint when test keys are set.
- **Vercel Production only:** Use **live** keys (`pk_live_...`, `sk_live_...`) for real payments. Set `STRIPE_LIVE_MODE=true` on the backend in production so mock subscribe/activate endpoints are disabled.

| Environment        | Keys    | Behavior                    |
|--------------------|--------|-----------------------------|
| Local / Preview / Dev | Test   | Test cards, no real charges |
| Vercel Production  | Live   | Real payments               |

If **no** Stripe publishable key is set, the app uses a **mock** flow (no Stripe; for first-time setup or demos).

## 📱 Testing

### Test Stripe Checkout

1. Go to `/pricing`
2. Click "Get Started" on any plan
3. Modal opens with Stripe checkout embedded (or mock flow if no key)
4. Use test card **4242 4242 4242 4242** when in test mode, or complete mock “Pay now”

### Test Calendly Booking

1. Go to home page (`/`)
2. Click "Book a Demo" button
3. Modal opens with Calendly scheduler
4. Select time or close modal

## 🔧 Customization

### Change Calendly URL

Update in `frontend/components/Hero.tsx`:

```typescript
<CalendlyBooking
  isOpen={showCalendlyModal}
  onClose={() => setShowCalendlyModal(false)}
  calendlyUrl="https://calendly.com/your-new-link"  // ← Change here
/>
```

### Change Stripe Links

Update in `frontend/lib/data.ts` in the `PricingPlans` object:

```typescript
{
  type: "Starter",
  price: "$249",
  stripeLink: "https://buy.stripe.com/your-new-link",  // ← Change here
  features: [...]
}
```

## ✅ Advantages of This Approach

1. **No Setup Required** - Works immediately, no API keys
2. **Secure** - Stripe and Calendly handle all sensitive data
3. **Maintained** - Stripe/Calendly update their checkout/booking UI
4. **PCI Compliant** - No payment data touches your server
5. **Simple** - Just wrap existing links in premium design

## 🚀 What's Next

The integration is **ready to use** right now!

Optional enhancements:

- Add success/cancel redirect URLs to Stripe links
- Customize Calendly embed parameters
- Add analytics tracking for conversions
- Customize modal animations further

---

**Status**: ✅ Ready to Use  
**Setup Time**: 0 minutes (no configuration needed)  
**Design**: 🎨 Premium Glassmorphic UI
