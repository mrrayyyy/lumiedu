"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRequireRole } from "@/lib/hooks/use-require-role";
import {
  createUser,
  deleteUser,
  listUsers,
  updateUser,
} from "@/lib/api";
import { ROLE_LABELS } from "@/lib/auth-context";
import type { Role, UserSummary } from "@/lib/types";

const ROLES: Role[] = ["admin", "teacher", "student", "parent"];

export default function AdminUsersPage() {
  const { token, isAuthenticated } = useRequireRole(["admin"]);
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    email: "",
    password: "",
    role: "student" as Role,
    full_name: "",
    grade_level: "",
  });
  const [creating, setCreating] = useState(false);

  const load = async () => {
    if (!token) return;
    try {
      const data = await listUsers(token);
      setUsers(data.users);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the tai");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await listUsers(token);
        if (cancelled) return;
        setUsers(data.users);
        setError("");
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Khong the tai");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function handleCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!token) return;
    setCreating(true);
    setError("");
    try {
      await createUser(token, {
        email: createForm.email.trim(),
        password: createForm.password,
        role: createForm.role,
        full_name: createForm.full_name.trim(),
        grade_level: createForm.grade_level.trim() || null,
      });
      setShowCreate(false);
      setCreateForm({ email: "", password: "", role: "student", full_name: "", grade_level: "" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the tao");
    } finally {
      setCreating(false);
    }
  }

  async function handleToggleActive(user: UserSummary) {
    if (!token) return;
    try {
      await updateUser(token, user.email, { is_active: !user.is_active });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the cap nhat");
    }
  }

  async function handleChangeRole(user: UserSummary, newRole: Role) {
    if (!token || newRole === user.role) return;
    try {
      await updateUser(token, user.email, { role: newRole });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the cap nhat");
    }
  }

  async function handleDelete(user: UserSummary) {
    if (!token) return;
    if (!confirm(`Xoa nguoi dung ${user.email}?`)) return;
    try {
      await deleteUser(token, user.email);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Khong the xoa");
    }
  }

  if (!isAuthenticated) return null;

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quan ly nguoi dung</h1>
          <p className="mt-1 text-sm text-gray-500">
            Tao, chinh sua, va phan quyen tai khoan
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowCreate(!showCreate)}
          className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          {showCreate ? "Dong" : "Them nguoi dung"}
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="mb-6 grid grid-cols-1 gap-4 rounded-xl border border-indigo-200 bg-indigo-50 p-6 sm:grid-cols-2"
        >
          <div>
            <label htmlFor="user-email" className="mb-1 block text-sm font-medium text-gray-700">Email</label>
            <input
              id="user-email"
              required
              value={createForm.email}
              onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="user-name" className="mb-1 block text-sm font-medium text-gray-700">Ho ten</label>
            <input
              id="user-name"
              value={createForm.full_name}
              onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="user-password" className="mb-1 block text-sm font-medium text-gray-700">Mat khau</label>
            <input
              id="user-password"
              type="password"
              required
              minLength={6}
              value={createForm.password}
              onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="user-role" className="mb-1 block text-sm font-medium text-gray-700">Vai tro</label>
            <select
              id="user-role"
              value={createForm.role}
              onChange={(e) => setCreateForm({ ...createForm, role: e.target.value as Role })}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABELS[r]}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="user-grade" className="mb-1 block text-sm font-medium text-gray-700">Khoi/Lop (tuy chon)</label>
            <input
              id="user-grade"
              value={createForm.grade_level}
              onChange={(e) => setCreateForm({ ...createForm, grade_level: e.target.value })}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
              placeholder="VD: grade6"
            />
          </div>
          <div className="sm:col-span-2 flex justify-end gap-2">
            <button
              type="submit"
              disabled={creating}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {creating ? "Dang tao..." : "Tao"}
            </button>
          </div>
        </form>
      )}

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Ho ten</th>
              <th className="px-4 py-3">Vai tro</th>
              <th className="px-4 py-3">Lop</th>
              <th className="px-4 py-3">Trang thai</th>
              <th className="px-4 py-3 text-right">Hanh dong</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  Dang tai...
                </td>
              </tr>
            )}
            {!loading && users.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  Chua co nguoi dung
                </td>
              </tr>
            )}
            {users.map((u) => (
              <tr key={u.email}>
                <td className="px-4 py-3 font-medium text-gray-900">{u.email}</td>
                <td className="px-4 py-3 text-gray-700">{u.full_name || "-"}</td>
                <td className="px-4 py-3">
                  <select
                    aria-label={`Vai tro cho ${u.email}`}
                    value={u.role}
                    onChange={(e) => handleChangeRole(u, e.target.value as Role)}
                    className="rounded-md border border-gray-300 bg-white px-2 py-1 text-xs"
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {ROLE_LABELS[r]}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3 text-gray-700">{u.grade_level || "-"}</td>
                <td className="px-4 py-3">
                  <button
                    type="button"
                    onClick={() => handleToggleActive(u)}
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      u.is_active
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-gray-200 text-gray-600"
                    }`}
                  >
                    {u.is_active ? "Hoat dong" : "Khoa"}
                  </button>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    onClick={() => handleDelete(u)}
                    className="text-xs text-red-600 hover:text-red-800"
                  >
                    Xoa
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
