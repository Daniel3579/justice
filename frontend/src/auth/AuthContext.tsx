import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { authApi, clearToken, getToken, type User } from "../api/auth";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // При загрузке страницы восстанавливаем сессию по сохранённому токену.
  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    await authApi.login(email, password);
    setUser(await authApi.me());
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    await authApi.register(email, password);
    setUser(await authApi.me());
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  const deleteAccount = useCallback(async () => {
    await authApi.deleteAccount();
    clearToken();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, deleteAccount }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth должен использоваться внутри AuthProvider");
  return ctx;
}
