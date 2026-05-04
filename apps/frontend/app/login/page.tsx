"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { login as apiLogin } from "@/lib/api";

const DEMO_ACCOUNTS: { label: string; email: string; password: string }[] = [
  { label: "Quan tri vien", email: "admin@lumiedu.local", password: "Admin123!" },
  { label: "Giao vien", email: "teacher@lumiedu.local", password: "Demo123!" },
  { label: "Hoc sinh", email: "student@lumiedu.local", password: "Demo123!" },
  { label: "Phu huynh", email: "parent@lumiedu.local", password: "Demo123!" },
];

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("admin@lumiedu.local");
  const [password, setPassword] = useState("Admin123!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiLogin(email, password);
      login(data.access_token, data.email, data.role, data.full_name);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dang nhap that bai");
    } finally {
      setLoading(false);
    }
  }

  function fillDemo(demoEmail: string, demoPassword: string) {
    setEmail(demoEmail);
    setPassword(demoPassword);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 text-2xl font-bold text-white shadow-lg">
            L
          </div>
          <h1 className="text-3xl font-bold text-gray-900">LumiEdu</h1>
          <p className="mt-2 text-gray-600">
            Gia su AI Toan lop 6 - Hoc qua giong noi
          </p>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
          <h2 className="mb-6 text-xl font-semibold text-gray-900">Dang nhap</h2>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-gray-700">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
                placeholder="email@example.com"
                required
              />
            </div>
            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-gray-700">
                Mat khau
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
                placeholder="Nhap mat khau"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading || !email || !password}
              className="w-full rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:from-indigo-700 hover:to-purple-700 focus:ring-2 focus:ring-indigo-200 focus:outline-none disabled:opacity-50"
            >
              {loading ? "Dang xu ly..." : "Dang nhap"}
            </button>
          </form>

          <div className="mt-6 border-t border-gray-100 pt-4">
            <p className="mb-2 text-xs font-medium text-gray-500">
              Dang nhap nhanh tai khoan demo:
            </p>
            <div className="flex flex-wrap gap-2">
              {DEMO_ACCOUNTS.map((d) => (
                <button
                  key={d.email}
                  type="button"
                  onClick={() => fillDemo(d.email, d.password)}
                  className="rounded-full border border-gray-300 bg-white px-3 py-1 text-xs text-gray-700 hover:border-indigo-400 hover:bg-indigo-50"
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-gray-500">
          LumiEdu MVP - Gia su AI the he moi, thau hieu qua giong noi
        </p>
      </div>
    </div>
  );
}
