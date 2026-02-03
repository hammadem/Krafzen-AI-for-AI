import { fireEvent, render, screen } from "@testing-library/react"
import Faqs from "@/app/(main)/faqs/page";
import { faqs } from "@/lib/data";

describe("FAQs Page", () => {
    it("renders the Faq Page", () => {
        render(<Faqs />);

        const buttons = faqs.map(faq => {
            const foundButtons = screen.getAllByRole("button", { name: faq.type });
            expect(foundButtons[0]).toBeInTheDocument();
            return foundButtons[0];
        });

        buttons.map((button, ind) => {
            fireEvent.click(button);

            const activeHeaders = screen.getAllByRole("button", { name: faqs[ind].type });
            expect(activeHeaders[0]).toBeInTheDocument();

            faqs[ind].QandA.map(qanda => {
                expect(screen.getAllByText(qanda.question)[0]).toBeInTheDocument();
                qanda.answer.map(ans => {
                    expect(screen.getAllByText(ans)[0]).toBeInTheDocument();
                })
            })
        })
    });
})