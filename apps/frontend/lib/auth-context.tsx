"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";

type AuthState = {
  token: string;
  email: string;
  isAuthenticated: boolean;
  login: (token: string, email: string) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

const TOKEN_KEY = "lumiedu_token";
const EMAIL_KEY = "lumiedu_email";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem(TOKEN_KEY) ?? "";
  });
  const [email, setEmail] = useState(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem(EMAIL_KEY) ?? "";
  });

  const loginFn = useCallback((newToken: string, newEmail: string) => {
    setToken(newToken);
    setEmail(newEmail);
    localStorage.setItem(TOKEN_KEY, newToken);
    localStorage.setItem(EMAIL_KEY, newEmail);
  }, []);

  const logout = useCallback(() => {
    setToken("");
    setEmail("");
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
  }, []);

  const value = useMemo(
    () => ({
      token,
      email,
      isAuthenticated: token.length > 0,
      login: loginFn,
      logout,
    }),
    [token, email, loginFn, logout],
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
