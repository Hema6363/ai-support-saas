const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export interface User {
  id: number;
  tenant_id: number;
  email: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user?: User;
}

export interface DocumentItem {
  id: number;
  tenant_id: number;
  owner_id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  status: "PENDING" | "PROCESSING" | "PROCESSED" | "FAILED";
  error_message?: string;
  created_at?: string;
}

export interface Citation {
  document_id?: number;
  filename: string;
  chunk_index: number;
  snippet: string;
  distance: number;
}

export interface Message {
  id: number;
  conversation_id: number;
  tenant_id: number;
  sender_id?: number;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: string;
  latency_ms?: number;
  created_at?: string;
}

export interface Conversation {
  id: number;
  tenant_id: number;
  user_id: number;
  document_id?: number;
  title: string;
  created_at?: string;
  updated_at?: string;
  messages?: Message[];
}

export interface Ticket {
  id: number;
  tenant_id: number;
  user_id: number;
  conversation_id?: number;
  title: string;
  description: string;
  status: "open" | "in_progress" | "resolved" | "closed";
  priority: "low" | "medium" | "high" | "urgent";
  is_resolved: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AnalyticsDashboard {
  total_conversations: number;
  total_messages: number;
  total_tickets: number;
  resolved_tickets: number;
  resolution_rate_pct: number;
  avg_messages_per_conversation: number;
  avg_ai_latency_ms: number;
  total_documents: number;
  total_document_chunks: number;
  ticket_status_breakdown: {
    open: number;
    in_progress: number;
    resolved: number;
    closed: number;
  };
  activity_trend: {
    date: string;
    conversations: number;
    messages: number;
    tickets: number;
  }[];
  top_documents: {
    id: number;
    filename: string;
    chunk_count: number;
    file_size: number;
    created_at?: string;
  }[];
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  price_monthly: number;
  currency: string;
  max_documents: number;
  max_queries_per_month: number;
  features: string[];
}

export interface SubscriptionStatus {
  tenant_id: number;
  plan: string;
  status: string;
  documents_used: number;
  documents_limit: number;
  queries_used: number;
  queries_limit: number;
  is_active: boolean;
}

// Token storage helpers
export const getAccessToken = (): string | null => {
  if (typeof window === "undefined") return null;
  const token =
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    localStorage.getItem("auth_token") ||
    sessionStorage.getItem("access_token") ||
    sessionStorage.getItem("token") ||
    null;
  if (!token) return null;
  return token.replace(/^"(.*)"$/, "$1").trim();
};

export const getRefreshToken = (): string | null => {
  if (typeof window === "undefined") return null;
  const token =
    localStorage.getItem("refresh_token") ||
    sessionStorage.getItem("refresh_token") ||
    null;
  if (!token) return null;
  return token.replace(/^"(.*)"$/, "$1").trim();
};

export const setTokens = (tokens: AuthTokens | { access_token?: string; token?: string; refresh_token?: string }) => {
  if (typeof window === "undefined" || !tokens) return;
  const access = (tokens as any).access_token || (tokens as any).token;
  const refresh = (tokens as any).refresh_token;
  if (access) {
    const cleanAccess = String(access).replace(/^"(.*)"$/, "$1").trim();
    localStorage.setItem("access_token", cleanAccess);
    localStorage.setItem("token", cleanAccess);
  }
  if (refresh) {
    const cleanRefresh = String(refresh).replace(/^"(.*)"$/, "$1").trim();
    localStorage.setItem("refresh_token", cleanRefresh);
  }
};

export const clearTokens = () => {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("token");
  localStorage.removeItem("auth_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user_info");
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("token");
  sessionStorage.removeItem("refresh_token");
};

// Automatic Token Refresh Helper
async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    clearTokens();
    return null;
  }
  try {
    const url = `${API_BASE}/auth/refresh`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) {
      clearTokens();
      return null;
    }
    const data: AuthTokens = await res.json();
    setTokens(data);
    return data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}

function formatValidationError(detail: any): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((err) => {
        const field = Array.isArray(err.loc) ? err.loc.slice(1).join(".") : "field";
        return `${field ? field + ": " : ""}${err.msg || "Invalid value"}`;
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }
  return "Validation error";
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  let token = getAccessToken();
  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;

  // If no access token exists but refresh token is available, attempt proactive refresh
  if (!token && getRefreshToken() && !normalizedEndpoint.startsWith("/auth/")) {
    token = await refreshAccessToken();
  }

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const url = `${API_BASE}${normalizedEndpoint}`;
  let response: Response;

  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (networkError: any) {
    // Distinguish network connection / CORS failures from application logic
    const method = options.method || "GET";
    throw new Error(
      `Network Error: Failed to reach backend at ${API_BASE} (${method} ${normalizedEndpoint}). Ensure backend is active and CORS is permitted.`
    );
  }

  // Handle 401: attempt transparent token refresh and retry original request
  if (
    response.status === 401 &&
    !normalizedEndpoint.startsWith("/auth/login") &&
    !normalizedEndpoint.startsWith("/auth/register") &&
    !normalizedEndpoint.startsWith("/auth/refresh")
  ) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      const retryHeaders: Record<string, string> = {
        ...headers,
        Authorization: `Bearer ${newToken}`,
      };
      try {
        response = await fetch(url, {
          ...options,
          headers: retryHeaders,
        });
      } catch (retryNetworkErr: any) {
        throw new Error(
          `Network Error on retry: Failed to reach backend at ${API_BASE} (${options.method || "GET"} ${normalizedEndpoint}).`
        );
      }
    } else {
      clearTokens();
    }
  }

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = formatValidationError(errorJson.detail);
      }
    } catch {
      // response was not JSON
    }

    if (response.status === 401) {
      throw new Error(`Authentication required (401): ${errorDetail}`);
    } else if (response.status === 403) {
      throw new Error(`Forbidden (403): ${errorDetail}`);
    } else if (response.status === 404) {
      throw new Error(`Resource not found (404): ${errorDetail}`);
    } else if (response.status === 422) {
      throw new Error(`Validation error (422): ${errorDetail}`);
    } else if (response.status >= 500) {
      throw new Error(`Server error (${response.status}): ${errorDetail}`);
    }

    throw new Error(errorDetail);
  }

  return response.json();
}
