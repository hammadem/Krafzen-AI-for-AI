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

    type HistoryData = {
        date: string,
        searches: {
            title: string,
            time: string | undefined
        }[]

    }
}
