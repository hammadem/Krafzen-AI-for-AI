import { render, screen, fireEvent } from "@testing-library/react";
import Navbar from "@/components/Navbar";
import { vi } from 'vitest';

// Mock the AuthContext
vi.mock("@/context/AuthContext", () => ({
  useAuth: () => ({
    user: null,
    logout: vi.fn(),
  }),
}));

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

describe("Navbar Component", () => {
  it("renders company name and navigation links", () => {
    render(<Navbar />);

    expect(screen.getAllByAltText("Your Company")[0]).toBeInTheDocument();
    expect(screen.getAllByAltText("Your Company")[1]).toBeInTheDocument();

    // Check all navigation links
    const links = ["About", "Features", "Pricing", "FAQs", "Support"];
    links.forEach((link) => {
      expect(screen.getAllByText(link)[0]).toBeInTheDocument();
    });

    // Check Start Free Trial button
    expect(screen.getAllByRole("link", { name: /start free trial/i })[0]).toBeInTheDocument();
  });

  it("toggles mobile menu when clicked", async () => {
    render(<Navbar />);

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
