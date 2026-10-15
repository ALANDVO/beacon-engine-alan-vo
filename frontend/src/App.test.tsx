import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import { useAuth } from "./hooks/useAuth";

vi.mock("./hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

vi.mock("./api/client", () => ({
  healthApi: {
    check: vi.fn().mockResolvedValue({ data: { status: "ok", version: "1.0.0", environment: "development" } }),
  },
  usersApi: {
    me: vi.fn().mockResolvedValue({ data: { id: "demo-user", email: "demo@local", name: "Demo User", roles: ["admin"] } }),
  },
}));

const renderApp = () => {
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
};

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as vi.Mock).mockReturnValue({ user: { id: "demo-user", name: "Demo User" }, loading: false });
  });

  it("renders dashboard when authenticated", async () => {
    renderApp();
    await waitFor(() => {
      const headings = screen.getAllByRole("heading", { name: "Dashboard", level: 1 });
      expect(headings.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("shows loading spinner when not authenticated", () => {
    (useAuth as vi.Mock).mockReturnValue({ user: null, loading: true });
    renderApp();
    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });
});

describe("Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as vi.Mock).mockReturnValue({ user: { id: "demo-user", name: "Demo User" }, loading: false });
  });

  it("shows system information cards", async () => {
    renderApp();
    await waitFor(() => {
      expect(screen.getByText("System Information")).toBeInTheDocument();
      expect(screen.getByText("Version")).toBeInTheDocument();
      expect(screen.getByText("Environment")).toBeInTheDocument();
    });
  });
});

describe("Navigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as vi.Mock).mockReturnValue({ user: { id: "demo-user", name: "Demo User" }, loading: false });
  });

  it("has navigation links", async () => {
    renderApp();
    await waitFor(() => {
      expect(screen.getByRole("link", { name: "ISOs" })).toBeInTheDocument();
      expect(screen.getByRole("link", { name: "Recipes" })).toBeInTheDocument();
      expect(screen.getByRole("link", { name: "Builds" })).toBeInTheDocument();
      const settingsLinks = screen.getAllByRole("link", { name: "Settings" });
      expect(settingsLinks.length).toBeGreaterThanOrEqual(1);
    });
  });
});