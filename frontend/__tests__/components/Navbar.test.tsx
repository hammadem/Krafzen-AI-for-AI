import { render, screen, fireEvent } from "@testing-library/react";
import Navbar from "@/components/Navbar";

describe("Navbar Component", () => {
  it("renders company name and navigation links", () => {
    render(<Navbar isRoot={true} />);

    expect(screen.getAllByAltText("Your Company")[0]).toBeInTheDocument();
    expect(screen.getAllByAltText("Your Company")[1]).toBeInTheDocument();

    // Check all navigation links
    const links = ["About", "Features", "Pricing", "FAQs", "Support"];
    links.forEach((link) => {
      expect(screen.getAllByText(link)[0]).toBeInTheDocument();
    });

    // Check Start Free Trial button
    expect(screen.getAllByText(/Start Free Trial/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Start Free Trial/i)[1]).toBeInTheDocument();

    // expect(screen.getAllByRole("button", { name: /Start Free Trial/i })[0]).toBeInTheDocument();
  });

  it("toggles mobile menu when clicked", async () => {
    render(<Navbar isRoot={true} />);

    const desktopMenu = screen.getByTestId("desktop-menu");
    expect(desktopMenu).toHaveClass("hidden");

    // Initially menu should be closed (opacity-0 class)
    const mobileMenu = screen.getByTestId("mobile-menu");
    expect(mobileMenu).toHaveClass("opacity-0");

    // // Click the mobile toggle button
    const toggleBtn = await screen.findByAltText("Toggle Button");
    fireEvent.click(toggleBtn);

    // // After click, it should now have 'opacity-100' class
    expect(mobileMenu).toHaveClass("opacity-100");
  });
});
