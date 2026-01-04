import NavHeader from "@/components/NavHeader";
import SupportForm from "@/components/SupportForm";

export default function Support() {
    return (
        <>
            <NavHeader currentNav="Support" />

            <div className="w-full min-h-[60vh] flex items-center justify-center bg-black py-12 px-4">
                <SupportForm />
            </div>
        </>
    )
}