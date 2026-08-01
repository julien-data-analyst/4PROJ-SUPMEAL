// composables/useApi.ts
import { useToken } from "./useToken";

interface FetchErrorLike {
  statusCode?: number;
}

function isFetchErrorLike(error: unknown): error is FetchErrorLike {
  return typeof error === "object" && error !== null && "statusCode" in error;
}

export const useApi = () => {
  const config = useRuntimeConfig();
  const apiBase = config.public.apiUrl || "http://localhost:8000/api";
  const { access, refresh } = useToken();

  const getHeaders = () => {
    const headers: Record<string, string> = {
      Accept: "application/json",
    };

    if (access.value) {
      headers["Authorization"] = `Bearer ${access.value}`;
    }

    return headers;
  };

  // Clears the local session only - the token that triggered a 401 is
  // already invalid/expired server-side, so there is nothing left to revoke.
  const clearSession = () => {
    access.value = null;
    refresh.value = null;

    if (import.meta.client) {
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      localStorage.removeItem("user");
    }
  };

  const handleError = (error: unknown): never => {
    console.error("Api Error:", error);

    if (isFetchErrorLike(error) && error.statusCode === 401) {
      clearSession();
      if (import.meta.client) {
        navigateTo("/login");
      }
    }

    throw error;
  };

  const get = async <T>(
    endpoint: string,
    options: Record<string, unknown> = {},
  ): Promise<T> => {
    try {
      return await $fetch<T>(`${apiBase}${endpoint}`, {
        method: "GET",
        headers: getHeaders(),
        ...options,
      });
    } catch (error) {
      return handleError(error);
    }
  };

  const post = async <T>(
    endpoint: string,
    data: Record<string, unknown> | FormData,
    options: Record<string, unknown> = {},
  ): Promise<T> => {
    try {
      const isFormData = data instanceof FormData;
      return await $fetch<T>(`${apiBase}${endpoint}`, {
        method: "POST",
        body: data,
        headers: {
          ...getHeaders(),
          ...(isFormData ? {} : { "Content-Type": "application/json" }),
          ...(options.headers as Record<string, string> | undefined),
        },
        ...options,
      });
    } catch (error) {
      return handleError(error);
    }
  };

  const put = async <T>(
    endpoint: string,
    data: Record<string, unknown> | FormData,
    options: Record<string, unknown> = {},
  ): Promise<T> => {
    try {
      const isFormData = data instanceof FormData;
      return await $fetch<T>(`${apiBase}${endpoint}`, {
        method: "PUT",
        body: data,
        headers: {
          ...getHeaders(),
          ...(isFormData ? {} : { "Content-Type": "application/json" }),
          ...(options.headers as Record<string, string> | undefined),
        },
        ...options,
      });
    } catch (error) {
      return handleError(error);
    }
  };

  const patch = async <T>(
    endpoint: string,
    data: Record<string, unknown> | FormData,
    options: Record<string, unknown> = {},
  ): Promise<T> => {
    try {
      const isFormData = data instanceof FormData;
      return await $fetch<T>(`${apiBase}${endpoint}`, {
        method: "PATCH",
        body: data,
        headers: {
          ...getHeaders(),
          ...(isFormData ? {} : { "Content-Type": "application/json" }),
          ...(options.headers as Record<string, string> | undefined),
        },
        ...options,
      });
    } catch (error) {
      return handleError(error);
    }
  };

  const del = async <T = void>(
    endpoint: string,
    data?: Record<string, unknown> | FormData,
    options: Record<string, unknown> = {},
  ): Promise<T> => {
    try {
      return await $fetch<T>(`${apiBase}${endpoint}`, {
        method: "DELETE",
        headers: {
          ...getHeaders(),
          ...(data ? { "Content-Type": "application/json" } : {}),
          ...(options.headers as Record<string, string> | undefined),
        },
        ...(data !== undefined ? { body: data } : {}),
        ...options,
      });
    } catch (error) {
      return handleError(error);
    }
  };

  const extractMembers = <T>(response: Record<string, unknown>): T[] => {
    return (response.results || []) as T[];
  };

  const extractData = <T>(
    response: Record<string, unknown>,
    key: string,
  ): T | null => {
    return (response[key] || null) as T | null;
  };

  return {
    get,
    post,
    put,
    patch,
    del,
    extractMembers,
    extractData,
  };
};
