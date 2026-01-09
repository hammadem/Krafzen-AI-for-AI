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

