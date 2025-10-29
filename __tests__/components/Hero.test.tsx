import {render, screen} from "@testing-library/react"
import Hero from "@/components/Hero";

describe("Hero Component", () => {
    it("renders the Hero section", async () => {
        const hero = await Hero();
        render(hero);

        //check if the image has been rendered
        const bgImage = await screen.findByAltText("Hero Image");
        expect(bgImage).toBeInTheDocument();
    })
});