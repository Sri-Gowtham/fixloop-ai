import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { AuthLayout, SsoButton } from "@/components/fixloop/AuthLayout";
import { FxButton } from "@/components/fixloop/Button";
import { supabase } from "@/lib/supabase";

export const Route = createFileRoute("/sign-up")({
  head: () => ({ meta: [{ title: "Create account · FixLoop AI" }] }),
  component: SignUpPage,
});

function SignUpPage() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!agreed) {
      setError("Please agree to the Terms and Privacy Policy.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);

    const { error: authError } = await supabase.auth.signUp({
      email: email.trim(),
      password,
      options: {
        data: {
          full_name: fullName.trim(),
          company: company.trim(),
        },
      },
    });

    setLoading(false);

    if (authError) {
      setError(authError.message);
      return;
    }

    // Sign up succeeded — navigate to dashboard (Supabase may require email confirmation
    // depending on project settings; the session will be set automatically if not required).
    navigate({ to: "/dashboard" });
  }

  return (
    <AuthLayout
      eyebrow="Start free · 14-day pilot"
      title="Create your workspace"
      subtitle="Connect your ticketing stack and watch the agent surface your first root-cause cluster within minutes."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/signin" className="text-primary font-semibold hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 gap-2">
          <SsoButton provider="google">Sign up with Google</SsoButton>
          <SsoButton provider="microsoft">Sign up with Microsoft</SsoButton>
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

        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
              Full name
            </div>
            <input
              type="text"
              placeholder="Nadia Khan"
              autoComplete="name"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full h-11 rounded-md border border-border bg-surface px-3 text-sm outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
            />
          </label>
          <label className="block">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
              Company
            </div>
            <input
              type="text"
              placeholder="Acme Corp"
              autoComplete="organization"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="w-full h-11 rounded-md border border-border bg-surface px-3 text-sm outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
            />
          </label>
        </div>

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

        <label className="block">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
            Password
          </div>
          <input
            type="password"
            placeholder="At least 8 characters"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full h-11 rounded-md border border-border bg-surface px-3 text-sm outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
          />
        </label>

        <label className="flex items-start gap-2 text-xs text-muted-foreground">
          <input
            type="checkbox"
            className="mt-0.5 accent-primary"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
          />
          <span>
            I agree to the{" "}
            <a className="text-primary hover:underline" href="#">
              Terms
            </a>{" "}
            and{" "}
            <a className="text-primary hover:underline" href="#">
              Privacy Policy
            </a>
            .
          </span>
        </label>

        <FxButton
          size="lg"
          variant="cyber"
          className="w-full"
          disabled={loading}
        >
          {loading ? "Creating workspace…" : "Create workspace"}
        </FxButton>
      </form>
    </AuthLayout>
  );
}
