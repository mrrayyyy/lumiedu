"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import type { Role } from "@/lib/types";

export function useRequireRole(allowed: Role[]) {
  const router = useRouter();
  const auth = useAuth();

  useEffect(() => {
    if (!auth.isAuthenticated) {
      router.push("/login");
      return;
    }
    if (allowed.length > 0 && !allowed.includes(auth.role)) {
      router.push("/dashboard");
    }
  }, [auth.isAuthenticated, auth.role, allowed, router]);

  return auth;
}
