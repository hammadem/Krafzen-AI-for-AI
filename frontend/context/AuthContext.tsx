import { createClient } from "@/app/lib/supabase/supabaseClient";
import { createContext, useContext, useState, ReactNode, useEffect } from "react";

interface AuthContextType {
  user: string | null | Session,
  loading: boolean,
  setLoading: (loading: boolean) => void,
  logout: () => void
}
interface Session {
  access_token: string;
  // ...other fields
}


// ✅ Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ✅ Create the provider
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<string | null | Session>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const supabase = createClient();

  // ✅ Check the current session
  // const getSession = async () => {
  //   const {
  //     data: { session },
  //   } = await supabase.auth.getSession();
  //   setUser(session?.access_token || null);
  //   setLoading(false);
  // };

  // ✅ Listen for real-time auth changes
  useEffect(() => {
    const fetchSession = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      console.log(session);
      setUser(session?.access_token || null);
      setLoading(false);
    };

    fetchSession(); // called asynchronously, no sync setState
  });


  // ✅ Logout function
  // Yet to be implemented
  const logout = async () => {
    await supabase.auth.signOut();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        setLoading,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// ✅ Custom hook for consuming the context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within a AuthProvider");
  }
  return context;
};
