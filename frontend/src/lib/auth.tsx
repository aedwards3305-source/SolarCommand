"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, ApiError } from "./api";

const COOKIE_MAX_AGE = 60 * 60 * 8; // 8 hours

function syncTokenCookie(token: string) {
  document.cookie = `token=${token}; path=/; SameSite=Lax; max-age=${COOKIE_MAX_AGE}`;
}

function clearTokenCookie() {
  document.cookie = "token=; path=/; max-age=0";
}

interface User {
  id: number;
  email: string;
  name: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  hasToken: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  hasToken: false,
  login: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasToken, setHasToken] = useState(() =>
    typeof window !== "undefined" ? !!localStorage.getItem("token") : false
  );

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setHasToken(false);
      setLoading(false);
      return;
    }
    setHasToken(true);
    // Sync cookie immediately so middleware won't redirect during navigation
    syncTokenCookie(token);
    api
      .me()
      .then((u) => {
        setUser(u);
      })
      .catch((err) => {
        // Only clear token on actual auth failures (401/403)
        // Network errors or server issues should not log the user out
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
          localStorage.removeItem("token");
          clearTokenCookie();
          setHasToken(false);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.login(email, password);
    localStorage.setItem("token", res.access_token);
    syncTokenCookie(res.access_token);
    setHasToken(true);
    setUser({
      id: res.user_id,
      email: res.email,
      name: res.name,
      role: res.role,
    });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    clearTokenCookie();
    setHasToken(false);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, hasToken, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
