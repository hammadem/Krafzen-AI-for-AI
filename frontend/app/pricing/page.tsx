import Pricing from "@/components/Pricing"
import NavHeader from "@/components/NavHeader"

export default function Pricings() {
    return (
        <>
            <NavHeader currentNav={"Pricing"} />

            <div className="mt-10">
                <Pricing />
            </div>
        </>
    )
}