import { createClient } from "@/lib/supabase/supabaseClient";
import { createContext, useContext, useState, useEffect, useRef, ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { getApiBaseUrl } from "@/lib/api/utils";
import { clearCache } from "@/lib/api/cache";
import { authLinkError } from "@/lib/auth/emailLinks";

interface AuthContextType {
  user: User | null; // ← from your global types
  session: Session | null;
  // this is for session managment you cannot manipulate this directly
  loading: boolean;
  accessError?: string | null;
  logout: () => void;
  currentProject: ProjectDetails | false | null;
  setCurrentProject: (value: ProjectDetails | false | null) => void;
  setUser: (value: User) => void;
  /** Refetch subscription/balance from backend and update user (plan, requests). */
  refreshSubscription: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const supabase = createClient();

  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [accessError, setAccessError] = useState<string | null>(null);
  const principal = useRef<string | null>(null);
  const authEpoch = useRef(0);
  const [currentProject, setCurrentProject] = useState<ProjectDetails | false | null>(null);

  const updateUserFromSubscriptionStatus = (data: {
    subscription?: { plan_name?: string; status?: string; trial_end_date?: string | null; plan_requests_total?: number };
    balance?: {
      trial_requests?: number;
      plan_requests?: number;
      subscription_status?: string;
      plan_name?: string;
      can_make_request?: boolean;
      can_access_workspace?: boolean;
      in_free_signup_tier?: boolean;
    };
  }, token: string) => {
    const sub = data.subscription || {};
    const balance = data.balance || {};
    const planNameRaw = sub.plan_name || balance.plan_name || "free";
    const planName = typeof planNameRaw === "string" ? planNameRaw.toLowerCase() : "free";
    const status = sub.status || balance.subscription_status || "inactive";
    const planReq = balance.plan_requests ?? 0;
    const planTotal = sub.plan_requests_total ?? 0;
    // Frontend is advisory only. The backend enforces paid entitlements for
    // every protected API route, even if the user modifies this state.
    const hasPaidSubscription = balance.can_access_workspace === true;
    const canAccessWorkspace = hasPaidSubscription;
    const displayPlan =
      planName === "free" ? "Free" : planName.charAt(0).toUpperCase() + planName.slice(1);
    setUser((prev) =>
      prev?.access_token === token
        ? {
            ...prev,
            subscription_plan: displayPlan,
            has_active_subscription: hasPaidSubscription,
            can_access_workspace: canAccessWorkspace,
            subscription_status: status,
            trial_requests_remaining: 0,
            plan_requests_remaining: planReq,
            plan_requests_total: planTotal,
            trial_end_date: sub.trial_end_date ?? undefined,
            in_free_signup_tier: false,
          }
        : prev
    );
  };

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let request: AbortController | undefined;
    const url = new URL(window.location.href);
    // A Site URL fallback may land on the home page rather than the callback.
    // Forward only known auth errors; never forward arbitrary redirect targets.
    if (url.pathname === "/" && authLinkError(url)) {
      window.location.replace("/auth/callback?error_code=" + encodeURIComponent(authLinkError(url)!));
      return;
    }
    const adopt = (next: Session | null) => {
      if (!active) return;
      const epoch = ++authEpoch.current;
      if (timer) clearTimeout(timer);
      request?.abort();
      const id = next?.user.id ?? null;
      if (id !== principal.current) {
        clearCache();
        setCurrentProject(null);
        principal.current = id;
      }
      setSession(next);
      setAccessError(null);
      if (!next?.access_token || !id) {
        setUser(null);
        setLoading(false);
        return;
      }
      const token = next.access_token;
      const metadata = next.user.user_metadata;
      setUser({
        userId: id, email: next.user.email,
        access_token: token,
        firstname: metadata?.firstname || metadata?.full_name?.split(" ")[0],
        lastname: metadata?.lastname || metadata?.full_name?.split(" ").slice(1).join(" "),
        avatar_url: metadata?.avatar_url || metadata?.picture,
        subscription_plan: "Free", can_access_workspace: false, has_active_subscription: false,
        remaining_minutes: 0, total_minutes_purchased: 0,
      });
      setLoading(true);
      const controller = new AbortController();
      request = controller;
      // Leave Supabase's auth-event lock before doing async work.
      timer = setTimeout(async () => {
        try {
          const response = await fetch(`${getApiBaseUrl()}/api/v1/payments/subscription-status`, {
            headers: { Authorization: `Bearer ${token}` }, cache: "no-store",
            signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]),
          });
          if (!response.ok) throw new Error("Account access could not be verified.");
          const data = await response.json();
          if (typeof data?.balance?.can_access_workspace !== "boolean") throw new Error("Account access response incomplete.");
          if (active && epoch === authEpoch.current) updateUserFromSubscriptionStatus(data, token);
        } catch {
          if (active && epoch === authEpoch.current) setAccessError("Account access could not be verified. Retry or sign in again.");
        } finally {
          if (active && epoch === authEpoch.current) setLoading(false);
        }
      }, 0);
    };
    let receivedEvent = false;
    const { data: listener } = supabase.auth.onAuthStateChange((_event, next) => {
      receivedEvent = true;
      adopt(next);
    });
    // Also support clients that cannot deliver an initial auth event.
    void supabase.auth.getSession().then(({ data }) => {
      if (!receivedEvent) adopt(data.session ?? null);
    }).catch(() => { if (!receivedEvent) adopt(null); });
    return () => {
      active = false;
      ++authEpoch.current;
      if (timer) clearTimeout(timer);
      request?.abort();
      listener.subscription.unsubscribe();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const resetAuthState = () => {
    setLoading(false);
    setCurrentProject(null);
  };

  const refreshSubscription = async (): Promise<boolean> => {
    // A Stripe redirect query parameter is NOT proof of payment. Read the
    // authenticated, webhook-updated subscription record instead.
    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const currentSession = sessionData?.session;
      if (!currentSession?.access_token) return false;
      const res = await fetch(`${getApiBaseUrl()}/api/v1/payments/subscription-status`, {
        headers: { Authorization: `Bearer ${currentSession.access_token}` },
        cache: "no-store",
      });
      if (!res.ok) return false;
      const data = await res.json();
      if (!data || typeof data !== "object" || !data.subscription || !data.balance) {
        return false;
      }
      updateUserFromSubscriptionStatus(data, currentSession.access_token);
      setAccessError(null);
      return data.balance.can_access_workspace === true;
    } catch (err) {
      console.error("Failed to verify subscription status:", err);
      return false;
    }
  };

  const logout = async () => {
    clearCache();
    ++authEpoch.current;
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
        accessError,
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

export const useOptionalAuth = () => useContext(AuthContext);
