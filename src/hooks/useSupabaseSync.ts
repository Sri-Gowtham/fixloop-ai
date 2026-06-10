import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";

/**
 * Custom hook to subscribe to Supabase realtime changes for a specific table
 * and automatically invalidate the provided React Query keys when changes occur.
 */
export function useSupabaseSync(
  table: string,
  queryKeysToInvalidate: ReadonlyArray<unknown>[],
  event: "INSERT" | "UPDATE" | "DELETE" | "*" = "*",
) {
  const queryClient = useQueryClient();

  const serializedKeys = JSON.stringify(queryKeysToInvalidate);

  useEffect(() => {
    // Create a Supabase channel for this table
    const channel = supabase
      .channel(`public:${table}`)
      .on("postgres_changes", { event, schema: "public", table }, (payload) => {
        // Invalidate all associated query keys so React Query refetches automatically
        queryKeysToInvalidate.forEach((key) => {
          queryClient.invalidateQueries({ queryKey: key });
        });
      })
      .subscribe();

    return () => {
      // Cleanup the subscription when the component unmounts
      supabase.removeChannel(channel);
    };
  }, [table, event, serializedKeys, queryClient]);
}
