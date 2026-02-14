// src/__tests__/Home.test.tsx
import { render, screen } from "@testing-library/react";
import Home from "../app/page";
import { vi } from 'vitest';

// Mock the imported components so we test only Home layout/structure
vi.mock("@/components/Hero", () => ({
  default: () => <div data-testid="hero">Mock Hero</div>,
}));

vi.mock("@/components/ContactCTA", () => ({
  default: () => <div data-testid="contact-cta">Mock ContactCTA</div>,
}));

vi.mock("@/components/Footer", () => ({
  default: () => <div data-testid="footer">Mock Footer</div>,
}));

describe("Home Page", () => {
  it("renders Navbar and Hero components", () => {
    render(<Home />);

    // Assertions
    expect(screen.getByTestId("hero")).toBeInTheDocument();
    expect(screen.getByTestId("contact-cta")).toBeInTheDocument();
    expect(screen.getByTestId("footer")).toBeInTheDocument();
  });
});
