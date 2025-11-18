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
    let mounted = true;

    const loadSession = async () => {
      const { data } = await supabase.auth.getSession();
      if (!mounted) return;

      const sessionData = data.session || null;
      setSession(sessionData);

      if (sessionData?.user) {
        // Build your custom User type
        setUser({
          userId: sessionData.user.id,
          email: sessionData.user.email || undefined,
          access_token: sessionData.access_token,
        });
      } else {
        setUser(null);
      }

      setLoading(false);
    };

    loadSession();

    // Listen for changes
    const { data: authListener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session);

        if (session?.user) {
          setUser({
            userId: session.user.id,
            email: session.user.email || undefined,
            access_token: session.access_token,
          });
          setCurrentProject(undefined);
        } else {
          setUser(null);
        }
      }
    );

    return () => {
      mounted = false;
      authListener.subscription.unsubscribe();
    };
  }, [supabase.auth]);

  const logout = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
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
