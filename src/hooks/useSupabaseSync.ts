import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";

/**
 * Custom hook to subscribe to Supabase realtime changes for a specific table
 * and automatically invalidate the provided React Query keys when changes occur.
 *
 * IMPORTANT: This hook is intentionally fail-safe.
 * A WebSocket / Realtime failure must NEVER:
 *   - throw an unhandled error
 *   - set React Query isError = true
 *   - prevent pages from rendering
 *
 * Realtime is an optional enhancement. The primary data source is the FastAPI
 * backend. If Supabase Realtime is unavailable, pages still load normally via
 * REST polling through React Query's staleTime / refetchInterval.
 */
export function useSupabaseSync(
  table: string,
  queryKeysToInvalidate: ReadonlyArray<unknown>[],
  event: "INSERT" | "UPDATE" | "DELETE" | "*" = "*",
) {
  const queryClient = useQueryClient();
  const serializedKeys = JSON.stringify(queryKeysToInvalidate);

  useEffect(() => {
    // DISABLED: Supabase Realtime subscriptions are temporarily disabled.
    // Reason: WebSocket failures were poisoning React Query's isError state,
    // causing pages to render error states even when the REST API (FastAPI)
    // returns valid data. Re-enable once Supabase Realtime is verified stable.
    console.warn(
      `[useSupabaseSync] Realtime subscription for "${table}" is disabled. ` +
      "Data will still load via REST. Re-enable when Supabase Realtime is configured.",
    );
    return () => {};

    // --- ORIGINAL CODE (preserved for re-enabling) ---
    // let channel: ReturnType<typeof supabase.channel> | null = null;
    // try {
    //   channel = supabase
    //     .channel(`public:${table}`)
    //     .on("postgres_changes", { event, schema: "public", table }, () => {
    //       queryKeysToInvalidate.forEach((key) => {
    //         queryClient.invalidateQueries({ queryKey: key });
    //       });
    //     })
    //     .subscribe((status, err) => {
    //       if (err) {
    //         console.warn(`[useSupabaseSync] Subscription error for "${table}":`, err);
    //       }
    //     });
    // } catch (err) {
    //   console.warn(`[useSupabaseSync] Failed to subscribe to "${table}":`, err);
    // }
    // return () => {
    //   if (channel) {
    //     try { supabase.removeChannel(channel); } catch (_) {}
    //   }
    // };
  }, [table, event, serializedKeys, queryClient]);
}
