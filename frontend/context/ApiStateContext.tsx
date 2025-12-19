// different api state for different ongoing request will make it better in single object
//model
// apiState = {
//   "projects:fetch": { status: "success" },
//   "prompt:send": { status: "inprogress" },
//   "audio:upload": { status: "idle" }
// }

import { createContext, useContext, useState, ReactNode } from "react";

interface ApiStateContextType {
    status: ReqState;
    setStatus: (val: ReqState) => void;
    apiError: AppError | null;
    setApiError: (err: AppError) => void;
}

// ✅ Create the context
const ApiStateContext = createContext<ApiStateContextType | undefined>(undefined);

// ✅ Create the provider
export const ApiStateProvider = ({ children }: { children: ReactNode }) => {
    const [status, setStatus] = useState<ReqState>("idle");
    const [apiError, setApiError] = useState<AppError | null>(null);

    return (
        <ApiStateContext.Provider
            value={{
                status,
                setStatus,
                apiError,
                setApiError
            }}
        >
            {children}
        </ApiStateContext.Provider>
    );
};

// ✅ Custom hook for consuming the context
export const useApiStateProvider = () => {
    const context = useContext(ApiStateContext);
    if (!context) {
        throw new Error("useApiStateProvider must be used within a ApiStateProvider");
    }
    return context;
};
