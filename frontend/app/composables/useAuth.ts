// composables/useAuth.ts
import { useApi } from "./useAPI";
import { useToken } from "./useToken";

export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  profile_icon: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  user: User;
  access: string;
  refresh: string;
}

interface RefreshResponse {
  access: string;
  refresh?: string;
}

export const useAuth = () => {
  const { access, refresh } = useToken();
  const user = useState<User | null>("auth-user", () => null);
  const initialized = useState<boolean>("auth-initialized", () => false);

  const { post, get } = useApi();

  const isAuthenticated = computed(() => !!access.value);

  // Stores a fresh { user, access, refresh } triple, from a password login,
  // a registration, or an OAuth exchange - they all return the same shape.
  const setSession = (data: AuthResponse) => {
    user.value = data.user;
    access.value = data.access;
    refresh.value = data.refresh;
    initialized.value = true;

    if (import.meta.client) {
      localStorage.setItem("access", data.access);
      localStorage.setItem("refresh", data.refresh);
      localStorage.setItem("user", JSON.stringify(data.user));
    }
  };

  // Clears local session state only, without calling the backend - used
  // when the stored refresh token turns out to already be invalid/expired.
  const clearSession = () => {
    user.value = null;
    access.value = null;
    refresh.value = null;

    if (import.meta.client) {
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      localStorage.removeItem("user");
    }
  };

  const register = async (data: {
    username: string;
    email: string;
    password: string;
  }): Promise<User> => {
    const response = await post<AuthResponse>("/users/register/", data);
    setSession(response);
    return response.user;
  };

  const login = async (data: {
    email: string;
    password: string;
  }): Promise<User> => {
    const response = await post<AuthResponse>("/users/login/", data);
    setSession(response);
    return response.user;
  };

  // Exchanges the stored refresh token for a new access token. Simple JWT
  // rotates the refresh token on every call, so this also extends the
  // 30-minute inactivity window as long as it keeps being called.
  const refreshSession = async (): Promise<void> => {
    if (!refresh.value) {
      throw new Error("Aucun token de rafraîchissement disponible");
    }

    const response = await post<RefreshResponse>("/users/token/refresh/", {
      refresh: refresh.value,
    });

    access.value = response.access;
    if (response.refresh) {
      refresh.value = response.refresh;
    }

    if (import.meta.client) {
      localStorage.setItem("access", response.access);
      if (response.refresh) {
        localStorage.setItem("refresh", response.refresh);
      }
    }
  };

  // Revokes the tokens server-side (best effort) and clears the local
  // session. Does not navigate anywhere - the /logout page is the single
  // entry point that triggers this and stays put to show the confirmation.
  const logout = async (): Promise<void> => {
    if (access.value && refresh.value) {
      try {
        await post("/users/logout/", { refresh: refresh.value });
      } catch {
        // Token already invalid/expired server-side, still proceed with local cleanup
      }
    }

    clearSession();
  };

  // Rehydrates the session on app start. If a refresh token was persisted,
  // it is used to obtain a fresh access token (and the current user), which
  // covers the "reload the page while logged in" case end to end. Guarded by
  // `initialized` so the global route middleware only does this once per app
  // load instead of on every navigation.
  const initAuth = async (): Promise<void> => {
    if (!import.meta.client || initialized.value) return;
    initialized.value = true;

    const savedRefresh = localStorage.getItem("refresh");
    const savedUser = localStorage.getItem("user");

    if (savedUser && savedUser !== "undefined" && savedUser !== "null") {
      try {
        user.value = JSON.parse(savedUser);
      } catch {
        user.value = null;
      }
    }

    if (!savedRefresh) {
      clearSession();
      return;
    }

    refresh.value = savedRefresh;

    try {
      await refreshSession();
      user.value = await get<User>("/users/me/");
      localStorage.setItem("user", JSON.stringify(user.value));
    } catch {
      clearSession();
    }
  };

  return {
    user,
    isAuthenticated,
    register,
    login,
    logout,
    initAuth,
    refreshSession,
    setSession,
  };
};
