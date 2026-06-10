import { ReactNode } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { AuthProvider } from "@/context/AuthContext";

export function renderWithAuth(ui: ReactNode, options?: Omit<RenderOptions, "wrapper">) {
  return render(ui, {
    wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>,
    ...options,
  });
}
