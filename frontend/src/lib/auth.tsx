"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  login: (password: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  isAuthenticated: false,
  login: async () => false,
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    // Check stored token on mount
    const stored = localStorage.getItem("xcom_token");
    const expiry = localStorage.getItem("xcom_token_expiry");
    if (stored && expiry && Date.now() / 1000 < Number(expiry)) {
      setToken(stored);
    }
    setChecked(true);
  }, []);

  const login = async (password: string): Promise<boolean> => {
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });

      if (!res.ok) return false;

      const data = await res.json();
      setToken(data.token);
      localStorage.setItem("xcom_token", data.token);
      localStorage.setItem("xcom_token_expiry", String(data.expires_at));
      return true;
    } catch {
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    localStorage.removeItem("xcom_token");
    localStorage.removeItem("xcom_token_expiry");
  };

  if (!checked) {
    return null; // Don't render until we check stored token
  }

  return (
    <AuthContext.Provider
      value={{ token, isAuthenticated: !!token, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
