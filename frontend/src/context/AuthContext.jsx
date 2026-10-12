import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("user");
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem("token") || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function verifySession() {
      if (token) {
        try {
          const profile = await api.auth.me();
          setUser(profile);
          localStorage.setItem("user", JSON.stringify(profile));
        } catch {
          logout();
        }
      }
      setLoading(false);
    }
    verifySession();
  }, [token]);

  const login = async (username, password) => {
    const res = await api.auth.login({ username, password });
    localStorage.setItem("token", res.access_token);
    setToken(res.access_token);
    const userInfo = {
      id: res.user_id,
      username: res.username,
      role: res.role,
    };
    setUser(userInfo);
    localStorage.setItem("user", JSON.stringify(userInfo));
    return userInfo;
  };

  const logout = () => {
    try {
      api.auth.logout();
    } catch {}
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    isAdmin: user?.role === "admin",
    login,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
