"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import type { Role } from "./types";

type AuthState = {
  token: string;
  email: string;
  role: Role;
  fullName: string;
  isAuthenticated: boolean;
  login: (token: string, email: string, role: Role, fullName: string) => void;
  logout: () => void;
  setProfile: (role: Role, fullName: string) => void;
};

const AuthContext = createContext<AuthState | null>(null);

const TOKEN_KEY = "lumiedu_token";
const EMAIL_KEY = "lumiedu_email";
const ROLE_KEY = "lumiedu_role";
const NAME_KEY = "lumiedu_full_name";

const DEFAULT_ROLE: Role = "admin";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem(TOKEN_KEY) ?? "";
  });
  const [email, setEmail] = useState(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem(EMAIL_KEY) ?? "";
  });
  const [role, setRole] = useState<Role>(() => {
    if (typeof window === "undefined") return DEFAULT_ROLE;
    const v = localStorage.getItem(ROLE_KEY);
    return (v as Role) ?? DEFAULT_ROLE;
  });
  const [fullName, setFullName] = useState(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem(NAME_KEY) ?? "";
  });

  const loginFn = useCallback(
    (newToken: string, newEmail: string, newRole: Role, newFullName: string) => {
      setToken(newToken);
      setEmail(newEmail);
      setRole(newRole);
      setFullName(newFullName);
      localStorage.setItem(TOKEN_KEY, newToken);
      localStorage.setItem(EMAIL_KEY, newEmail);
      localStorage.setItem(ROLE_KEY, newRole);
      localStorage.setItem(NAME_KEY, newFullName);
    },
    [],
  );

  const logout = useCallback(() => {
    setToken("");
    setEmail("");
    setRole(DEFAULT_ROLE);
    setFullName("");
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
    localStorage.removeItem(ROLE_KEY);
    localStorage.removeItem(NAME_KEY);
  }, []);

  const setProfile = useCallback((newRole: Role, newFullName: string) => {
    setRole(newRole);
    setFullName(newFullName);
    localStorage.setItem(ROLE_KEY, newRole);
    localStorage.setItem(NAME_KEY, newFullName);
  }, []);

  const value = useMemo(
    () => ({
      token,
      email,
      role,
      fullName,
      isAuthenticated: token.length > 0,
      login: loginFn,
      logout,
      setProfile,
    }),
    [token, email, role, fullName, loginFn, logout, setProfile],
  );

  return <AuthContext value={value}>{children}</AuthContext>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

export const ROLE_LABELS: Record<Role, string> = {
  admin: "Quan tri vien",
  teacher: "Giao vien",
  student: "Hoc sinh",
  parent: "Phu huynh",
};
