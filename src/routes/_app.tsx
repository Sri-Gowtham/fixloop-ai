import { createFileRoute, redirect } from "@tanstack/react-router";
import { AppShell } from "@/components/fixloop/AppShell";
import { supabase } from "@/lib/supabase";

export const Route = createFileRoute("/_app")({
  /**
   * This beforeLoad runs before ANY child route (_app/dashboard, _app/clusters, etc.)
   * is rendered.  If there is no active Supabase session, the user is redirected to
   * /signin immediately — they cannot reach the dashboard or any protected page.
   */
  beforeLoad: async ({ location }) => {
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      throw redirect({
        to: "/signin",
        search: { redirect: location.href },
      });
    }
  },
  component: AppShell,
});
