import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AuthLayout, AuthInput, SsoButton } from "@/components/fixloop/AuthLayout";
import { FxButton } from "@/components/fixloop/Button";

export const Route = createFileRoute("/sign-up")({
  head: () => ({ meta: [{ title: "Create account · FixLoop AI" }] }),
  component: SignUpPage,
});

function SignUpPage() {
  const navigate = useNavigate();
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
      <form
        onSubmit={(e) => {
          e.preventDefault();
          navigate({ to: "/dashboard" });
        }}
        className="space-y-4"
      >
        <div className="grid grid-cols-1 gap-2">
          <SsoButton provider="google">Sign up with Google</SsoButton>
          <SsoButton provider="microsoft">Sign up with Microsoft</SsoButton>
        </div>
        <div className="flex items-center gap-3 text-[10px] uppercase tracking-wider text-muted-foreground">
          <div className="h-px flex-1 bg-border" />
          or
          <div className="h-px flex-1 bg-border" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <AuthInput label="Full name" placeholder="Nadia Khan" autoComplete="name" />
          <AuthInput label="Company" placeholder="Acme Corp" autoComplete="organization" />
        </div>
        <AuthInput
          label="Work email"
          type="email"
          placeholder="you@company.com"
          autoComplete="email"
        />
        <AuthInput
          label="Password"
          type="password"
          placeholder="At least 12 characters"
          autoComplete="new-password"
        />
        <label className="flex items-start gap-2 text-xs text-muted-foreground">
          <input type="checkbox" className="mt-0.5 accent-primary" defaultChecked />
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
        <FxButton size="lg" variant="cyber" className="w-full">
          Create workspace
        </FxButton>
      </form>
    </AuthLayout>
  );
}
