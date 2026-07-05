import { createContext, useContext, useState, ReactNode } from "react";

export interface DashRoutes {
  settings: "settings",
  billing: "billing",
  exports: "exports",
  templates: "templates",
  projects: "projects",
  home: "home",
  activity: "activity",
  notifications: "notifications",
  members: "members",
  archive: "archive"
}

interface DashboardContextType {
  isUserActing: boolean;
  setUserAction: (value: boolean) => void;
  sideBarOpen: boolean;
  setSideBarOpen: (value: boolean) => void;
  route: Partial<DashRoutes>;
  setCurrentRoute: (value: Partial<DashRoutes>) => void;
  resetDashboardState: () => void;
  monthly: boolean;
  setMonthly: (val: boolean) => void;
}

// ✅ Create the context
const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

// ✅ Create the provider
export const DashboardProvider = ({ children }: { children: ReactNode }) => {
  const [isUserActing, setUserAction] = useState(false);
  const [sideBarOpen, setSideBarOpen] = useState(false);
  const [route, setCurrentRoute] = useState<Partial<DashRoutes>>({ home: "home" });
  const [monthly, setMonthly] = useState<boolean>(true);

  const resetDashboardState = () => {
    setSideBarOpen(false);
    setUserAction(false);
    setCurrentRoute({ home: "home" });
  }

  return (
    <DashboardContext.Provider
      value={{
        isUserActing,
        setUserAction,
        sideBarOpen,
        setSideBarOpen,
        route,
        setCurrentRoute,
        resetDashboardState,
        monthly,
        setMonthly
      }}
    >
      {children}
    </DashboardContext.Provider>
  );
};

// ✅ Custom hook for consuming the context
export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboard must be used within a DashboardProvider");
  }
  return context;
};
