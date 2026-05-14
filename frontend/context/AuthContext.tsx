import { createClient } from "@/lib/supabase/supabaseClient";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import type { Session, AuthChangeEvent } from "@supabase/supabase-js";
import { getApiBaseUrl } from "@/lib/api/utils";

interface AuthContextType {
  user: User | null; // ← from your global types
  session: Session | null;
  // this is for session managment you cannot manipulate this directly
  loading: boolean;
  logout: () => void;
  currentProject: ProjectDetails | false | null;
  setCurrentProject: (value: ProjectDetails | false | null) => void;
  setUser: (value: User) => void;
  /** Refetch subscription/balance from backend and update user (plan, requests). */
  refreshSubscription: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const supabase = createClient();

  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentProject, setCurrentProject] = useState<ProjectDetails | false | null>(null);

  const updateUserFromSubscriptionStatus = (data: {
    subscription?: { plan_name?: string; status?: string; trial_end_date?: string | null; plan_requests_total?: number };
    balance?: {
      trial_requests?: number;
      plan_requests?: number;
      subscription_status?: string;
      plan_name?: string;
      can_make_request?: boolean;
      in_free_signup_tier?: boolean;
    };
  }) => {
    const sub = data.subscription || {};
    const balance = data.balance || {};
    const planNameRaw = sub.plan_name || balance.plan_name || "free";
    const planName = typeof planNameRaw === "string" ? planNameRaw.toLowerCase() : "free";
    const status = sub.status || balance.subscription_status || "inactive";
    const trialReq = balance.trial_requests ?? 0;
    const planReq = balance.plan_requests ?? 0;
    const planTotal = sub.plan_requests_total ?? 0;
    const paidStatuses = ["active", "trial", "past_due"];
    const hasPaidSubscription = planName !== "free" && paidStatuses.includes(status);
    const canAccessWorkspace =
      hasPaidSubscription || trialReq > 0 || planReq > 0;
    const displayPlan =
      planName === "free" ? "Free" : planName.charAt(0).toUpperCase() + planName.slice(1);
    setUser((prev) =>
      prev
        ? {
            ...prev,
            subscription_plan: displayPlan,
            has_active_subscription: hasPaidSubscription,
            can_access_workspace: canAccessWorkspace,
            subscription_status: status,
            trial_requests_remaining: trialReq,
            plan_requests_remaining: planReq,
            plan_requests_total: planTotal,
            trial_end_date: sub.trial_end_date ?? undefined,
            in_free_signup_tier: balance.in_free_signup_tier ?? planName === "free",
          }
        : null
    );
  };

  useEffect(() => {
    // 1️⃣ Load session on mount
    const loadSession = async () => {
      // 0️⃣ Catch OAuth code in URL and redirect to callback if we are on the home page
      // This happens if Supabase redirect whitelist defaults to Site URL instead of /auth/callback
      if (typeof window !== "undefined") {
        const url = new URL(window.location.href);
        const code = url.searchParams.get("code");
        if (code && url.pathname === "/") {
          window.location.href = `/auth/callback?code=${code}`;
          return;
        }
      }

      // Refresh session so we have a valid access_token (avoids 401 from expired token)
      try {
        await supabase.auth.refreshSession();
      } catch {
        // No session or refresh failed — getSession() below will still run
      }
      const { data } = await supabase.auth.getSession();
      setSession(data.session || null);

      if (data.session?.user && data.session?.access_token) {
        setUser({
          userId: data.session.user.id,
          email: data.session.user.email || undefined,
          access_token: data.session.access_token,
          firstname: data?.session?.user?.user_metadata?.firstname || data?.session?.user?.user_metadata?.full_name?.split(' ')[0],
          lastname: data?.session?.user?.user_metadata?.lastname || data?.session?.user?.user_metadata?.full_name?.split(' ').slice(1).join(' '),
          avatar_url: data?.session?.user?.user_metadata?.avatar_url || data?.session?.user?.user_metadata?.picture,
          subscription_plan: data?.session?.user?.user_metadata?.subscription_plan || "Free",
          remaining_minutes: 0,
          total_minutes_purchased: 0
        });
        const apiUrl = getApiBaseUrl();
        try {
          const subRes = await fetch(`${apiUrl}/api/v1/payments/subscription-status`, {
            headers: { Authorization: `Bearer ${data.session.access_token}` },
          });
          if (subRes.ok) {
            const subJson = await subRes.json();
            updateUserFromSubscriptionStatus(subJson);
          }
        } catch (err) {
          console.error("Failed to fetch subscription status:", err);
        }
      } else {
        setUser(null);
      }

      setLoading(false);
    };

    loadSession();

    // 2️⃣ Listen to auth changes (login, logout, refresh)
    const { data: listener } = supabase.auth.onAuthStateChange(async (_event: AuthChangeEvent, session: Session | null) => {
      setSession(session || null);

      if (session?.user && session?.access_token) {
        setUser({
          userId: session.user.id,
          email: session.user.email || undefined,
          access_token: session.access_token,
          firstname: session?.user?.user_metadata?.firstname || session?.user?.user_metadata?.full_name?.split(' ')[0],
          lastname: session?.user?.user_metadata?.lastname || session?.user?.user_metadata?.full_name?.split(' ').slice(1).join(' '),
          avatar_url: session?.user?.user_metadata?.avatar_url || session?.user?.user_metadata?.picture,
          subscription_plan: session?.user?.user_metadata?.subscription_plan || "Free",
          remaining_minutes: 0,
          total_minutes_purchased: 0
        });

        // 3️⃣ Fetch detailed profile and subscription status from Backend (only with valid token)
        const apiUrl = getApiBaseUrl();
        const token = session.access_token;

        // Fetch user profile
        fetch(`${apiUrl}/api/v1/users/profile`, {
          headers: { Authorization: `Bearer ${token}` },
        })
          .then(res => (res.status === 401 ? null : res.json()))
          .then(data => {
            if (data && typeof data === "object")
              setUser(prev => prev ? {
                ...prev,
                remaining_minutes: data.remaining_minutes,
                total_minutes_purchased: data.total_minutes_purchased,
                subscription_plan: data.plan_tier || prev.subscription_plan
              } : null);
          })
          .catch(() => {});

        // Fetch subscription status (backend returns { subscription, balance })
        fetch(`${apiUrl}/api/v1/payments/subscription-status`, {
          headers: { Authorization: `Bearer ${token}` },
        })
          .then(res => (res.status === 401 ? null : res.json()))
          .then(data => data && typeof data === "object" ? updateUserFromSubscriptionStatus(data) : undefined)
          .catch(() => {});

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
  };

  const refreshSubscription = async () => {
    const { data: sessionData } = await supabase.auth.getSession();
    const session = sessionData?.session;
    if (!session?.access_token) return;
    const apiUrl = getApiBaseUrl();
    try {
      const res = await fetch(`${apiUrl}/api/v1/payments/subscription-status`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      const data = await res.json();
      updateUserFromSubscriptionStatus(data);
    } catch (err) {
      console.error("Failed to refresh subscription:", err);
    }
  };

  const logout = async () => {
    setLoading(true);

    try {
      await supabase.auth.signOut();
    } catch (err) {
      console.warn("Supabase signOut failed (clearing local state anyway):", err);
    } finally {
      // Always clear local state and redirect so logout works even if signOut() fails (e.g. staging backend/network)
      setUser(null);
      setSession(null);
      resetAuthState();
      window.location.href = "/";
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
        setUser,
        refreshSubscription,
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
