import { apiClient } from "@/lib/api/utils";

const PAYMENT_URLS = {
    CREATE_CHECKOUT: () => `/api/v1/payments/create-checkout-session`,
    CREATE_EMBEDDED_CHECKOUT: () => `/api/v1/payments/create-embedded-checkout-session`,
    GET_SUBSCRIPTION_STATUS: () => `/api/v1/payments/subscription-status`,
    MOCK_SUBSCRIBE: () => `/api/v1/payments/mock-subscribe`,
    MOCK_ACTIVATE_PLAN: () => `/api/v1/payments/mock-activate-plan`,
} as const;

export interface CreateCheckoutRequest {
    plan_name: string;  // starter, professional, enterprise, enterprise_plus
    billing_cycle: string;  // monthly, annual
}

export interface SubscriptionStatus {
    subscription: {
        plan_name: string;
        billing_cycle: string;
        status: string;
        trial_start_date: string | null;
        trial_end_date: string | null;
        plan_requests_reset_date: string | null;
    };
    balance: {
        trial_requests: number;
        plan_requests: number;
        total_requests: number;
        can_make_request: boolean;
        subscription_status: string;
        plan_name: string;
    };
}

/**
 * Create a Stripe checkout session for a subscription plan
 */
export async function createCheckoutSession(
    user: User | null,
    planName: string,
    billingCycle: string
): Promise<{ url: string }> {
    const body: CreateCheckoutRequest = {
        plan_name: planName,
        billing_cycle: billingCycle,
    };

    const response = await apiClient("POST", PAYMENT_URLS.CREATE_CHECKOUT(), user, body as unknown as Record<string, unknown>);

    if (response.ok && response.data) {
        return response.data as unknown as { url: string };
    }

    throw new Error(response.error?.message || "Failed to create checkout session");
}

export interface CreateEmbeddedCheckoutRequest {
    plan_name: string;
    billing_cycle: string;
    return_url: string;
}

/**
 * Create an embedded Stripe Checkout session (payment form in-page).
 * Returns client_secret for use with Stripe Embedded Checkout.
 */
export async function createEmbeddedCheckoutSession(
    user: User | null,
    planName: string,
    billingCycle: string,
    returnUrl: string
): Promise<{ client_secret: string }> {
    const body: CreateEmbeddedCheckoutRequest = {
        plan_name: planName,
        billing_cycle: billingCycle,
        return_url: returnUrl,
    };

    const response = await apiClient("POST", PAYMENT_URLS.CREATE_EMBEDDED_CHECKOUT(), user, body as unknown as Record<string, unknown>);

    if (response.ok && response.data) {
        return response.data as unknown as { client_secret: string };
    }

    throw new Error(response.error?.message || "Failed to create embedded checkout session");
}

/**
 * Local dev only: create a subscription without Stripe (mock payment).
 * Backend allows this only when FRONTEND_URL is localhost / dev.
 * @param paymentCompleted If true, user gets package requests (simulates payment after trial).
 */
export async function mockSubscribe(
    user: User | null,
    planName: string,
    billingCycle: string,
    paymentCompleted: boolean = false
): Promise<{ ok: boolean }> {
    const body = { plan_name: planName, billing_cycle: billingCycle, payment_completed: paymentCompleted };
    const response = await apiClient("POST", PAYMENT_URLS.MOCK_SUBSCRIBE(), user, body);
    if (response.ok && response.data) {
        return response.data as unknown as { ok: boolean };
    }
    throw new Error(response.error?.message || "Mock subscribe failed");
}

/**
 * Local dev only: grant package requests after "payment" (user was on trial).
 */
export async function mockActivatePlan(user: User | null): Promise<{ ok: boolean }> {
    const response = await apiClient("POST", PAYMENT_URLS.MOCK_ACTIVATE_PLAN(), user, undefined);
    if (response.ok && response.data) {
        return response.data as unknown as { ok: boolean };
    }
    throw new Error(response.error?.message || "Mock activate plan failed");
}

/**
 * Get current subscription status and request balance
 */
export async function getSubscriptionStatus(
    user: User | null
): Promise<SubscriptionStatus> {
    const response = await apiClient("GET", PAYMENT_URLS.GET_SUBSCRIPTION_STATUS(), user);

    if (response.ok && response.data) {
        return response.data as unknown as SubscriptionStatus;
    }

    throw new Error(response.error?.message || "Failed to get subscription status");
}


/** Stripe invoices resolved server-side by the authenticated user's customer ID. */
export interface StripeInvoice {
    id: string;
    number: string | null;
    created: number | null;
    status: string | null;
    currency: string | null;
    amount_due: number | null;
    amount_paid: number | null;
    hosted_invoice_url: string | null;
    invoice_pdf: string | null;
}

export async function getCustomerInvoices(user: User | null): Promise<StripeInvoice[]> {
    const response = await apiClient("GET", "/api/v1/payments/invoices", user);
    if (!response.ok || !response.data) {
        throw new Error(response.error?.message || "Invoice history unavailable");
    }
    const body = response.data as unknown as { invoices?: StripeInvoice[] };
    if (!Array.isArray(body.invoices)) throw new Error("Invalid invoice response");
    return body.invoices;
}

export async function createBillingPortalSession(user: User | null): Promise<string> {
    const response = await apiClient("POST", "/api/v1/payments/portal-session", user);
    if (!response.ok || !response.data) {
        throw new Error(response.error?.message || "Billing portal unavailable");
    }
    const data = response.data as unknown as { url?: string };
    if (!data.url) throw new Error("Billing portal did not return a URL");
    const destination = new URL(data.url);
    if (destination.protocol !== "https:" ||
        (!destination.hostname.endsWith(".stripe.com") && destination.hostname !== "stripe.com")) {
        throw new Error("Billing portal returned an unsafe URL");
    }
    return destination.toString();
}
