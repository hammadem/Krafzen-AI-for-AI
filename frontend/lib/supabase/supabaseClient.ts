import { createBrowserClient } from '@supabase/ssr';

export function createClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!url || !anonKey) {
    // If we're missing keys (e.g. during build time pre-rendering), 
    // return a dummy client to prevent the build from crashing.
    return {
      auth: {
        getSession: async () => ({ data: { session: null }, error: null }),
        onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
        refreshSession: async () => ({ data: { session: null }, error: null }),
        signOut: async () => ({ error: null }),
        signInWithPassword: async () => ({ data: { user: null, session: null }, error: new Error("Supabase keys missing") }),
        signUp: async () => ({ data: { user: null, session: null }, error: new Error("Supabase keys missing") }),
        signInWithOAuth: async () => ({ data: { provider: "", url: "" }, error: new Error("Supabase keys missing") }),
      },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } as any;
  }

  return createBrowserClient(url, anonKey, {
    auth: { persistSession: true }
  });
}