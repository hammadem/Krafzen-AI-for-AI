import NavHeader from "@/components/NavHeader";
import SupportForm from "@/components/SupportForm";

export default function Support() {
    return (
        <>
            <NavHeader currentNav="Support" />

            <div className="w-full flex items-center justify-center bg-[#1d1c1cff] py-12 px-6">
                <SupportForm />

            </div>
        </>
    )
}