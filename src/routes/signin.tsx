import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AuthLayout, AuthInput, SsoButton } from "@/components/fixloop/AuthLayout";
import { FxButton } from "@/components/fixloop/Button";

export const Route = createFileRoute("/signin")({
  head: () => ({ meta: [{ title: "Sign in · FixLoop AI" }] }),
  component: SignInPage,
});

function SignInPage() {
  const navigate = useNavigate();
  return (
    <AuthLayout
      eyebrow="Welcome back"
      title="Sign in to FixLoop AI"
      subtitle="Pick up where the agent left off. Your investigations, fixes, and reports are waiting."
      footer={<>New to FixLoop AI? <Link to="/sign-up" className="text-primary font-semibold hover:underline">Create an account</Link></>}
    >
      <form onSubmit={(e) => { e.preventDefault(); navigate({ to: "/dashboard" }); }} className="space-y-4">
        <div className="grid grid-cols-1 gap-2">
          <SsoButton provider="google">Continue with Google</SsoButton>
          <SsoButton provider="microsoft">Continue with Microsoft</SsoButton>
        </div>
        <div className="flex items-center gap-3 text-[10px] uppercase tracking-wider text-muted-foreground">
          <div className="h-px flex-1 bg-border" />or<div className="h-px flex-1 bg-border" />
        </div>
        <AuthInput label="Work email" type="email" placeholder="you@company.com" autoComplete="email" />
        <div>
          <AuthInput label="Password" type="password" placeholder="••••••••" autoComplete="current-password" />
          <div className="mt-2 text-right">
            <Link to="/forgot-password" className="text-xs text-primary hover:underline">Forgot password?</Link>
          </div>
        </div>
        <FxButton size="lg" variant="cyber" className="w-full">Sign in</FxButton>
        <div className="text-[10px] text-mono uppercase tracking-wider text-muted-foreground text-center pt-1">
          Protected by SSO · MFA · SOC 2 Type II
        </div>
      </form>
    </AuthLayout>
  );
}