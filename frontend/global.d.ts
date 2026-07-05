export global {
    type PricingDetails = {
        type: string,
        price: string,
        features: string[]
        stripeLink?: string
    }

    type PricingPlans = {
        monthly: PricingDetails[],
        annual: PricingDetails[]
    }

    type AboutData = {
        heading: string,
        p: string[]
    }

    type FAQs = {
        type: string
        QandA: {
            question: string,
            answer: string[]
        }[]
    }

    type UserChat = string | null;

    interface Searches {
        title: string;
        time: string;
        isoTime: string;
        chats: UserChat;
        id: string;
    }

    interface HistoryData {
        iso: string;
        date: string;
        searches: Searches[];
    }

    interface User {
        access_token: string | null | undefined;
        userId: string | undefined;
        email: string | undefined;
        firstname: string | undefined?;
        lastname: string | undefined?;
        avatar_url: string | undefined?;
        subscription_plan: string | undefined?;
        remaining_minutes: number | undefined;
        total_minutes_purchased: number | undefined;
        // Subscription status fields
        has_active_subscription?: boolean;
        /** True if user may open workspace (paid plan or has free/package request balance). */
        can_access_workspace?: boolean;
        /** Backend: using signup free pool before first subscription. */
        in_free_signup_tier?: boolean;
        subscription_status?: string;
        trial_requests_remaining?: number;
        plan_requests_remaining?: number;
        plan_requests_total?: number;  // plan's included requests (e.g. 10000 for Enterprise)
        trial_end_date?: string | null;  // ISO date; used for "Trial: X days left"
        /** Workspace role. Week 1: stub (defaults to "owner"); real roles in Week 2. */
        role?: "owner" | "admin" | "member" | "viewer" | string;
    }

    interface Settings {
        profilename: string;
        email: string;
        password: string;
        notification: boolean;
        integrations: boolean;
        advancedsettings: {
            exportsettings: boolean;
            developerapikeys: boolean;
            importsettings: boolean;
        }
    }

    interface TemplateData {
        url: string,
        title: string,
        details: string
    }
}

