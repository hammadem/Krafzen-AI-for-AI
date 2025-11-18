import { createContext, useContext, useState, ReactNode } from "react";

interface DashRoutes {
  settings: "settings",
  billing: "billing",
  exports: "exports",
  templates: "templates",
  projects: "projects",
  home: "home"
}

interface DashboardContextType {
  input: string;
  setInput: (value: string) => void;
  audioUrl: string;
  setAudioURL: (value: string) => void;
  isRecording: boolean;
  setIsRecording: (value: boolean) => void;
  isUserActing: boolean;
  setUserAction: (value: boolean) => void;
  sideBarOpen: boolean;
  setSideBarOpen: (value: boolean) => void;
  file: string;
  setFile: (value: string) => void;
  isPrompt: boolean;
  setIsPromptSend: (value: boolean) => void;
  route: string | Partial<DashRoutes>;
  setCurrentRoute: (value: string) => void;
  history: HistoryData[];
  setHistory: (value: HistoryData[]) => void;
}

// ✅ Create the context
const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

// ✅ Create the provider
export const DashboardProvider = ({ children }: { children: ReactNode }) => {
  const [input, setInput] = useState("");
  const [audioUrl, setAudioURL] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isUserActing, setUserAction] = useState(false);
  const [sideBarOpen, setSideBarOpen] = useState(false);
  const [file, setFile] = useState("");
  const [isPrompt, setIsPromptSend] = useState<boolean>(false);
  const [route, setCurrentRoute] = useState("home");
  const [history, setHistory] = useState<HistoryData[]>([]);


  return (
    <DashboardContext.Provider
      value={{
        input,
        setInput,
        audioUrl,
        setAudioURL,
        isRecording,
        setIsRecording,
        isUserActing,
        setUserAction,
        sideBarOpen,
        setSideBarOpen,
        file,
        setFile,
        isPrompt,
        setIsPromptSend,
        route,
        setCurrentRoute,
        history,
        setHistory
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
