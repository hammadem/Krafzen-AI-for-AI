export global {
    type PricingDetails = {
        type: string,
        price: string,
        features: string[]
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
    }

    interface HistoryData {
        iso: string;
        date: string;
        searches: Searches[];
    }

    export interface ProjectDetails {
        created_at: string;
        dxf_url: string | null;
        id: string;
        input_text: string;
        parsed_json: JSON | null; // add here type when server starts responding 
        updated_at: string;
        user_id: string;
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

}
