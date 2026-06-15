import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import type { User } from "@supabase/supabase-js";

export interface AuthUser {
  /** Raw Supabase user object, null while loading or unauthenticated */
  user: User | null;
  /** Display-ready full name — from user_metadata, email prefix, or "User" */
  displayName: string;
  /** Initials (up to 2 chars) derived from displayName */
  initials: string;
  /** User's email or "No email" */
  email: string;
  /** True while the initial session fetch is in flight */
  loading: boolean;
}

function deriveDisplayName(user: User | null): string {
  if (!user) return "User";
  const meta = user.user_metadata as Record<string, unknown> | undefined;
  const fullName =
    (meta?.full_name as string | undefined) ||
    (meta?.name as string | undefined) ||
    "";
  if (fullName.trim()) return fullName.trim();
  // Fall back to the part of the email before @
  if (user.email) return user.email.split("@")[0];
  return "User";
}

function deriveInitials(displayName: string): string {
  const parts = displayName.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return displayName.slice(0, 2).toUpperCase();
}

/**
 * Returns the currently authenticated Supabase user together with
 * display-safe derived fields.  Stays reactive: updates on
 * signIn / signOut / token refresh via onAuthStateChange.
 */
export function useUser(): AuthUser {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch the current session immediately
    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user ?? null);
      setLoading(false);
    });

    // Stay in sync with auth state changes
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  const displayName = deriveDisplayName(user);

  return {
    user,
    displayName,
    initials: deriveInitials(displayName),
    email: user?.email ?? "No email",
    loading,
  };
}
