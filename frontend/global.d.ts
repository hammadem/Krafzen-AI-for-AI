export global {
    type PricingDetails = {
        type:string,
        price:string,
        features:string[]
    }

    type PricingPlans = {
        monthly: PricingDetails[],
        annual: PricingDetails[]
    }
}