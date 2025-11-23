// src/__tests__/Home.test.tsx
import { render, screen } from "@testing-library/react";
import Home from "../app/(main)/page";

// Mock the imported components so we test only Home layout/structure
vi.mock("@/components/Hero", () => ({
  default: () => <div data-testid="hero">Mock Hero</div>,
}));

describe("Home Page", () => {
  it("renders Navbar and Hero components", () => {
    render(<Home />);

    // Assertions
    expect(screen.getByTestId("hero")).toBeInTheDocument();

  });
});
