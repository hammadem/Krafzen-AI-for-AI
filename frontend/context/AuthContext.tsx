import { createClient } from "@/lib/supabase/supabaseClient";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { useRouter } from "next/navigation";

interface AuthContextType {
  user: User | null; // ← from your global types
  session: Session | null;
  // this is for session managment you cannot manipulate this directly
  loading: boolean;
  logout: () => void;
  currentProject: ProjectDetails | false | null;
  setCurrentProject: (value: ProjectDetails | false | null) => void;
  setUser: (value: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const supabase = createClient();
  const router = useRouter();

  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentProject, setCurrentProject] = useState<ProjectDetails | false | null>(null);

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
          firstname: data?.session?.user?.user_metadata?.firstname || data?.session?.user?.user_metadata?.full_name?.split(' ')[0],
          lastname: data?.session?.user?.user_metadata?.lastname || data?.session?.user?.user_metadata?.full_name?.split(' ').slice(1).join(' '),
          avatar_url: data?.session?.user?.user_metadata?.avatar_url || data?.session?.user?.user_metadata?.picture,
          subscription_plan: data?.session?.user?.user_metadata?.subscription_plan || "Free Trial",
          remaining_minutes: 0,
          total_minutes_purchased: 0
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
          firstname: session?.user?.user_metadata?.firstname || session?.user?.user_metadata?.full_name?.split(' ')[0],
          lastname: session?.user?.user_metadata?.lastname || session?.user?.user_metadata?.full_name?.split(' ').slice(1).join(' '),
          avatar_url: session?.user?.user_metadata?.avatar_url || session?.user?.user_metadata?.picture,
          subscription_plan: session?.user?.user_metadata?.subscription_plan || "Free Trial",
          remaining_minutes: 0,
          total_minutes_purchased: 0
        });

        // 3️⃣ Fetch detailed profile from Backend
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/users/profile`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`
          }
        })
          .then(res => res.json())
          .then(data => {
            setUser(prev => prev ? {
              ...prev,
              remaining_minutes: data.remaining_minutes,
              total_minutes_purchased: data.total_minutes_purchased,
              subscription_plan: data.plan_tier || prev.subscription_plan
            } : null);
          })
          .catch(err => console.error("Failed to fetch profile:", err));

      } else {

        setUser(null);
      }

      setLoading(false);
    });

    return () => listener.subscription.unsubscribe();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const resetAuthState = () => {
    setLoading(false);
    setCurrentProject(null);
  }

  const logout = async () => {
    setLoading(true);

    try {
      await supabase.auth.signOut();
      setUser(null);
      setSession(null);
      router.push("/");
    } catch (err) {
      console.log(err)
    } finally {
      resetAuthState();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        logout,
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
