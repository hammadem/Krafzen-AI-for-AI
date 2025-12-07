import { createContext, useContext, useState, ReactNode } from "react";

export interface DashRoutes {
  settings: "settings",
  billing: "billing",
  exports: "exports",
  templates: "templates",
  projects: "projects",
  home: "home"
}

interface DashboardContextType {
  isRecording: boolean;
  setIsRecording: (value: boolean) => void;
  isUserActing: boolean;
  setUserAction: (value: boolean) => void;
  sideBarOpen: boolean;
  setSideBarOpen: (value: boolean) => void;
  isPrompting: boolean;
  setisPromptingSend: (value: boolean) => void;
  route: Partial<DashRoutes>;
  setCurrentRoute: (value: Partial<DashRoutes>) => void;
  resetDashboardState: () => void;
}

// ✅ Create the context
const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

// ✅ Create the provider
export const DashboardProvider = ({ children }: { children: ReactNode }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isUserActing, setUserAction] = useState(false);
  const [sideBarOpen, setSideBarOpen] = useState(false);
  const [isPrompting, setisPromptingSend] = useState<boolean>(false);
  const [route, setCurrentRoute] = useState<Partial<DashRoutes>>({ home: "home" });

  const resetDashboardState = () => {
    setisPromptingSend(false);
    setSideBarOpen(false);
    setIsRecording(false);
    setUserAction(false);
    setCurrentRoute({ home: "home" });
  }

  return (
    <DashboardContext.Provider
      value={{
        isRecording,
        setIsRecording,
        isUserActing,
        setUserAction,
        sideBarOpen,
        setSideBarOpen,
        isPrompting,
        setisPromptingSend,
        route,
        setCurrentRoute,
        resetDashboardState
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
