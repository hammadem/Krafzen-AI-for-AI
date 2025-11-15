import { render, screen } from "@testing-library/react"
import About from "@/app/(main)/about/page";
import { aboutData } from "@/app/lib/data";

describe("About Page", () => {
    it("renders the About Page", () => {
        render(<About />);

        expect(screen.getByAltText("About Rectangle")).toBeInTheDocument();

        aboutData.map(about => {
            expect(screen.getByText(about.heading)).toBeInTheDocument();
            about.p.map(p => {
                expect(screen.getByText(p)).toBeInTheDocument();
            })
        })
    });
})