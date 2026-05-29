// Auth state, backed by GET /auth/google/me.
//
// `useAuth` is the single source of truth for "who is signed in". It calls /me
// once on load (with credentials); a 401 means anonymous and is treated as a
// normal "not signed in" state, not an error to retry.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError, API_BASE } from "../lib/api";

export interface Creator {
  id: number;
  email: string;
  display_name: string | null;
  channel_id: string | null;
}

export function useAuth() {
  const query = useQuery<Creator | null>({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      try {
        return await apiFetch<Creator>("/auth/google/me");
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) return null;
        throw err;
      }
    },
    staleTime: 5 * 60_000,
    retry: false,
  });

  return {
    creator: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    isAuthenticated: !!query.data,
  };
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<{ ok: boolean }>("/auth/google/logout", { method: "POST" }),
    onSuccess: () => {
      qc.setQueryData(["auth", "me"], null);
    },
  });
}

// The login link is a plain top-level navigation (not fetch) so the browser
// follows Google's redirect chain and can set the cookie on the way back.
export const loginUrl = `${API_BASE}/auth/google/login`;
