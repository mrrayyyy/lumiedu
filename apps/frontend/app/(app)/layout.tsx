"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";
import { useAuth } from "@/lib/auth-context";
import { getMe } from "@/lib/api";
import Sidebar from "@/components/sidebar";

export default function AppLayout({ children }: { children: ReactNode }) {
  const { isAuthenticated, token, role, fullName, setProfile } = useAuth();

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const me = await getMe(token);
        if (cancelled) return;
        if (me.role !== role || (me.full_name || "") !== fullName) {
          setProfile(me.role, me.full_name || "");
        }
      } catch {
        // ignore - user can re-login
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, role, fullName, setProfile]);

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
