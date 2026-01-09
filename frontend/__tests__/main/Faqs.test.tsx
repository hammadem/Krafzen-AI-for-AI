import { fireEvent, render, screen } from "@testing-library/react"
import Faqs from "@/app/(main)/faqs/page";
import { faqs } from "@/lib/data";

describe("FAQs Page", () => {
    it("renders the Faq Page", () => {
        render(<Faqs />);

        const buttons = faqs.map(faq => {
            expect(screen.getByRole("button", { name: faq.type })).toBeInTheDocument();

            return (
                screen.getByRole("button", { name: faq.type })
            );
        });

        buttons.map((button, ind) => {
            fireEvent.click(button);

            expect(screen.getByRole("button", { name: faqs[ind].type })).toBeInTheDocument();

            faqs[ind].QandA.map(qanda => {
                expect(screen.getByText(qanda.question)).toBeInTheDocument();
                qanda.answer.map(ans => {
                    expect(screen.getByText(ans)).toBeInTheDocument();
                })
            })
        })

    });
})