import { createClient } from "@/lib/supabase/supabaseClient";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";

interface AuthContextType {
  user: User | null; // ← from your global types
  session: Session | null;
  loading: boolean;
  logout: () => void;
  projects: ProjectDetails[];
  setProjects: (value: ProjectDetails[]) => void;
  currentProject: Searches | undefined;
  setCurrentProject: (value: Searches | undefined) => void;
  setUser: (value: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const supabase = createClient();

  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<ProjectDetails[]>([]);
  const [currentProject, setCurrentProject] = useState<Searches>();

  useEffect(() => {
    // 1️⃣ Load session on mount
    const loadSession = async () => {
      const { data } = await supabase.auth.getSession();
      setSession(data.session || null);

      if (data.session?.user) {
        setUser({
          userId: data.session.user.id,
          email: data.session.user.email || undefined,
          access_token: data.session.access_token,
          firstname: data?.session?.user?.user_metadata?.firstname,
          lastname: data?.session?.user?.user_metadata?.lastname
        });
      } else {
        setUser(null);
      }

      setLoading(false);
    };

    loadSession();

    // 2️⃣ Listen to auth changes (login, logout, refresh)
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session || null);

      if (session?.user) {
        setUser({
          userId: session.user.id,
          email: session.user.email || undefined,
          access_token: session.access_token,
          firstname: session?.user?.user_metadata?.firstname,
          lastname: session?.user?.user_metadata?.lastname
        });
      } else {
        setUser(null);
      }

      setLoading(false);
    });

    return () => listener.subscription.unsubscribe();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const logout = async () => {
    setLoading(true);
    try {
      await supabase.auth.signOut();
      setUser(null);
      setSession(null);
    } catch (err) {
      console.log(err)
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        logout,
        projects,
        setProjects,
        currentProject,
        setCurrentProject,
        setUser
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Hook
export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
