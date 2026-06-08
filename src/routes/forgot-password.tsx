import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { AuthLayout, AuthInput } from "@/components/fixloop/AuthLayout";
import { FxButton } from "@/components/fixloop/Button";
import { CheckCircle2, MailCheck } from "lucide-react";

export const Route = createFileRoute("/forgot-password")({
  head: () => ({ meta: [{ title: "Reset password · FixLoop AI" }] }),
  component: ForgotPasswordPage,
});

function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  return (
    <AuthLayout
      eyebrow="Account recovery"
      title={sent ? "Check your inbox" : "Reset your password"}
      subtitle={sent ? "We sent a secure reset link. It expires in 15 minutes." : "Enter the email tied to your workspace and we'll send a reset link."}
      footer={<>Back to <Link to="/signin" className="text-primary font-semibold hover:underline">Sign in</Link></>}
    >
      {sent ? (
        <div className="space-y-4">
          <div className="rounded-md border border-secondary/30 bg-secondary/5 p-4 flex items-start gap-3">
            <MailCheck className="h-5 w-5 text-secondary mt-0.5" />
            <div className="text-sm">
              <div className="font-semibold">Reset link sent</div>
              <div className="text-muted-foreground">Open the email and follow the link. Didn't receive it? Check spam or try again in 60s.</div>
            </div>
          </div>
          <ul className="space-y-2 text-xs text-muted-foreground">
            {["Link expires in 15 minutes", "Single-use token, encrypted at rest", "Audited under SOC 2 Type II"].map((t) => (
              <li key={t} className="flex items-center gap-2"><CheckCircle2 className="h-3.5 w-3.5 text-secondary" />{t}</li>
            ))}
          </ul>
          <FxButton size="lg" variant="outline" className="w-full" onClick={() => setSent(false)}>Use a different email</FxButton>
        </div>
      ) : (
        <form onSubmit={(e) => { e.preventDefault(); setSent(true); }} className="space-y-4">
          <AuthInput label="Work email" type="email" placeholder="you@company.com" autoComplete="email" />
          <FxButton size="lg" variant="cyber" className="w-full">Send reset link</FxButton>
        </form>
      )}
    </AuthLayout>
  );
}