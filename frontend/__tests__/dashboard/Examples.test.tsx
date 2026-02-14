import { render, screen } from "@testing-library/react"
import { Example, ExportHistory, Heading, NavLinks, SeePlans, TemplateBox } from "@/app/(dashboard)/_component/Examples";
import { PricingPlans, TemplateData } from "@/lib/data";
import { Accordion, AccordionItem } from "@/components/ui/accordion";

describe("Example components", () => {
    it("renders the Export History", () => {
        render(<ExportHistory ind={1} currentExp={1} />);

        expect(screen.getByRole("button", { name: /Download/i })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /Re-export/i })).toBeInTheDocument();

    });

    it("renders the Heading", () => {
        render(<Heading />);

        expect(screen.getByText(/What do you want to draw today?/i)).toBeInTheDocument();
    });

    it("renders the NavLinks", () => {
        render(<NavLinks setCurrentRoute={() => {}} />);

        expect(screen.getByRole("link", { name: /Home/i })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /Projects/i })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /Templates/i })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /Exports/i })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /Billing/i })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /Settings/i })).toBeInTheDocument();

    });

    it("renders Examples", () => {
        render(<Example ex={["first", "second"]} />);

        expect(screen.getByText(/first/i)).toBeInTheDocument();
        expect(screen.getByText(/second/i)).toBeInTheDocument();
    });

    it("renders SeePlans", () => {
        render(
            <Accordion
                type="single"
                collapsible
                className="w-full"
                defaultValue="item-1"
            >
                <AccordionItem value="item-1 flex">
                    <SeePlans ind={0} plan={PricingPlans.monthly[0]} />
                </AccordionItem>
            </Accordion>
        );

        expect(screen.getByText(/Starter/i)).toBeInTheDocument();
        expect(screen.getByText(/Basic features for individual use./i)).toBeInTheDocument();
        expect(screen.getByText(/\$249/i)).toBeInTheDocument();
        expect(screen.getByText(/Current Plan/i)).toBeInTheDocument();
    });

    it("renders TemplateBox", () => {
        render(<TemplateBox TemplateData={TemplateData} />);

        expect(screen.getAllByText(/Modern House/i)[0]).toBeInTheDocument();
        expect(screen.getByText(/A compact and efficient 2-bedroom modern house/i)).toBeInTheDocument();
        expect(screen.getAllByText(/Modern House/i)[0]).toBeInTheDocument();
    });
})