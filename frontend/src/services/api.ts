import type { ApiError } from './types';
const rawApiUrl = (import.meta.env.VITE_API_URL as string || 'http://localhost:8000/api/v1').trim();
export const API_BASE = rawApiUrl.replace(/([^:])\/+/g, '$1/').replace(/\/+$/, '');

export const getAccessToken = (): string | null => localStorage.getItem('access_token');
export const getRefreshToken = (): string | null => localStorage.getItem('refresh_token');

export const setTokens = (accessToken: string, refreshToken?: string): void => {
  localStorage.setItem('access_token', accessToken);
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken);
  }
};

export const clearTokens = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb);
};

const onTokenRefreshed = (token: string) => {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
};

export const parseApiError = async (res: Response): Promise<ApiError> => {
  let title = 'An error occurred';
  let detail = res.statusText || 'Unexpected server response';
  let type = undefined;
  let validationErrors: Record<string, string[]> | undefined = undefined;

  try {
    const data = await res.json();
    if (data.title) title = data.title;
    if (data.detail) {
      if (typeof data.detail === 'string') {
        detail = data.detail;
      } else if (Array.isArray(data.detail)) {
        detail = data.detail.map((d: any) => `${d.loc?.slice(-1)[0] || 'field'}: ${d.msg}`).join(', ');
        validationErrors = {};
        data.detail.forEach((d: any) => {
          const field = d.loc?.slice(-1)[0] || 'general';
          if (!validationErrors![field]) validationErrors![field] = [];
          validationErrors![field].push(d.msg);
        });
      }
    } else if (data.message) {
      detail = data.message;
    }
    if (data.type) type = data.type;
  } catch {
    // Non-JSON response
  }

  return {
    status: res.status,
    title,
    detail,
    type,
    validationErrors,
  };
};

export const fetchWithAuth = async <T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<{ data: T; error: null } | { data: null; error: ApiError }> => {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  const token = getAccessToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string>),
  };

  try {
    // Never leave the UI spinning forever if the backend or an upstream provider stalls.
    const timeoutMs = endpoint.startsWith('/ai/') ? 60_000 : 30_000;
    let response = await fetch(url, { signal: AbortSignal.timeout(timeoutMs), ...options, headers });

    // Handle 401 Unauthorized with token refresh rotation
    if (response.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/refresh')) {
      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        clearTokens();
        return {
          data: null,
          error: { status: 401, title: 'Unauthorized', detail: 'Session expired. Please log in.' },
        };
      }

      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          if (refreshRes.ok) {
            const refreshData = await refreshRes.json();
            const newAccessToken = refreshData.data?.access_token || refreshData.access_token;
            const newRefreshToken = refreshData.data?.refresh_token || refreshData.refresh_token;
            setTokens(newAccessToken, newRefreshToken);
            isRefreshing = false;
            onTokenRefreshed(newAccessToken);
          } else {
            isRefreshing = false;
            clearTokens();
            return {
              data: null,
              error: { status: 401, title: 'Session Expired', detail: 'Please log in again.' },
            };
          }
        } catch {
          isRefreshing = false;
          clearTokens();
          return {
            data: null,
            error: { status: 401, title: 'Session Expired', detail: 'Failed to refresh authentication session.' },
          };
        }
      }

      // Wait for active refresh to complete
      const retryPromise = new Promise<{ data: T; error: null } | { data: null; error: ApiError }>((resolve) => {
        subscribeTokenRefresh(async (newToken) => {
          headers['Authorization'] = `Bearer ${newToken}`;
          try {
            const retryRes = await fetch(url, { ...options, headers });
            if (retryRes.ok) {
              const resData = await retryRes.json();
              resolve({ data: (resData.data !== undefined ? resData.data : resData) as T, error: null });
            } else {
              const err = await parseApiError(retryRes);
              resolve({ data: null, error: err });
            }
          } catch {
            resolve({
              data: null,
              error: { status: 0, title: 'Network Error', detail: 'Network connectivity lost during request retry.' },
            });
          }
        });
      });

      return await retryPromise;
    }

    if (!response.ok) {
      const err = await parseApiError(response);
      return { data: null, error: err };
    }

    // Success response
    const json = await response.json();
    return { data: (json.data !== undefined ? json.data : json) as T, error: null };
  } catch (err: any) {
    return {
      data: null,
      error: {
        status: 0,
        title: 'Network Disconnected',
        detail: err.message || 'Unable to connect to the PHC Connect API server. Check your internet connection.',
      },
    };
  }
};

export const api = {
  get: <T = any>(endpoint: string, options?: RequestInit) =>
    fetchWithAuth<T>(endpoint, { method: 'GET', ...options }),
  post: <T = any>(endpoint: string, body?: any, options?: RequestInit) =>
    fetchWithAuth<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    }),
  patch: <T = any>(endpoint: string, body?: any, options?: RequestInit) =>
    fetchWithAuth<T>(endpoint, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    }),
  put: <T = any>(endpoint: string, body?: any, options?: RequestInit) =>
    fetchWithAuth<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    }),
  delete: <T = any>(endpoint: string, options?: RequestInit) =>
    fetchWithAuth<T>(endpoint, { method: 'DELETE', ...options }),
};
