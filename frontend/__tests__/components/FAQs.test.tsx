import { fireEvent, render, screen } from "@testing-library/react"
import FAQs from "@/components/FAQs";

describe("FAQs components", () => {
    it("renders the FAQs section", () => {
        render(<FAQs />);

        // check rendering of faqs questions
        const faqs = [
            {
                question: "What is Krafzen AI about?",
                answer:
                    "KRAFZEN AI is a SaaS platform that transforms natural voice or text instructions into accurate CAD/DXF/DWG/Revit/BIM MEP models and as-built/instrumentation drawings.",
            },
            {
                question: "What file formats does KRAFZEN AI support?",
                answer:
                    "You can export to DXF, DWG, Revit, and BIM formats. Enterprise plans also support custom exports.",
            },
            {
                question: "Is there a free plan?",
                answer:
                    "Yes. The Free Plan allows limited projects per month with basic exports (DXF/DWG). It's a great way to test the platform before upgrading.",
            },
        ];

        faqs.forEach((faq) => {
            expect(screen.getByText(faq.question)).toBeInTheDocument();

            const toggleAnswer = screen.getByText(faq.question);
            fireEvent.click(toggleAnswer);

            // check if answer is availaible
            expect(screen.getByText(faq.answer));
        })

        expect(screen.getByText(/Read more/i)).toBeInTheDocument();
    })
})