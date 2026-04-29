"use client";

import type { ReactNode } from "react";
import { useAuth } from "@/lib/auth-context";
import Sidebar from "@/components/sidebar";

export default function AppLayout({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
