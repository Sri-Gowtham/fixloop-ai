import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { AuthLayout, SsoButton } from "@/components/fixloop/AuthLayout";
import { FxButton } from "@/components/fixloop/Button";
import { supabase } from "@/lib/supabase";

export const Route = createFileRoute("/signin")({
  head: () => ({ meta: [{ title: "Sign in · FixLoop AI" }] }),
  component: SignInPage,
});

function SignInPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const { error: authError } = await supabase.auth.signInWithPassword({
      email: email.trim(),
      password,
    });

    setLoading(false);

    if (authError) {
      setError(authError.message);
      return;
    }

    navigate({ to: "/dashboard" });
  }

  return (
    <AuthLayout
      eyebrow="Welcome back"
      title="Sign in to FixLoop AI"
      subtitle="Pick up where the agent left off. Your investigations, fixes, and reports are waiting."
      footer={
        <>
          New to FixLoop AI?{" "}
          <Link to="/sign-up" className="text-primary font-semibold hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 gap-2">
          <SsoButton provider="google">Continue with Google</SsoButton>
          <SsoButton provider="microsoft">Continue with Microsoft</SsoButton>
        </div>
        <div className="flex items-center gap-3 text-[10px] uppercase tracking-wider text-muted-foreground">
          <div className="h-px flex-1 bg-border" />
          or
          <div className="h-px flex-1 bg-border" />
        </div>

        {error && (
          <div className="rounded-md border border-critical/40 bg-critical/10 px-3 py-2.5 text-sm text-critical">
            {error}
          </div>
        )}

        <label className="block">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
            Work email
          </div>
          <input
            type="email"
            placeholder="you@company.com"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full h-11 rounded-md border border-border bg-surface px-3 text-sm outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
          />
        </label>

        <div>
          <label className="block">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
              Password
            </div>
            <input
              type="password"
              placeholder="••••••••"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full h-11 rounded-md border border-border bg-surface px-3 text-sm outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
            />
          </label>
          <div className="mt-2 text-right">
            <Link to="/forgot-password" className="text-xs text-primary hover:underline">
              Forgot password?
            </Link>
          </div>
        </div>

        <FxButton
          size="lg"
          variant="cyber"
          className="w-full"
          disabled={loading}
        >
          {loading ? "Signing in…" : "Sign in"}
        </FxButton>

        <div className="text-[10px] text-mono uppercase tracking-wider text-muted-foreground text-center pt-1">
          Protected by SSO · MFA · SOC 2 Type II
        </div>
      </form>
    </AuthLayout>
  );
}
