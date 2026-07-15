import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

const ACCESS_KEY = "expense_access";
const REFRESH_KEY = "expense_refresh";

export const tokenStore = {
  access: () => localStorage.getItem(ACCESS_KEY),
  refresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = tokenStore.access();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 401 → refresh 시도 후 1회 재시도
let refreshing: Promise<string | null> | null = null;

async function doRefresh(): Promise<string | null> {
  const refresh = tokenStore.refresh();
  if (!refresh) return null;
  try {
    const res = await axios.post(`${API_BASE}/api/v1/auth/refresh`, {
      refresh_token: refresh,
    });
    tokenStore.set(res.data.access_token, res.data.refresh_token);
    return res.data.access_token;
  } catch {
    tokenStore.clear();
    return null;
  }
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      refreshing = refreshing ?? doRefresh();
      const newToken = await refreshing;
      refreshing = null;
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      }
      if (window.location.pathname !== "/login") window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ── API 함수 ──────────────────────────────────
export async function login(email: string, password: string) {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const res = await axios.post(`${API_BASE}/api/v1/auth/login`, form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data as { access_token: string; refresh_token: string };
}

export const endpoints = {
  me: () => api.get("/api/v1/auth/me").then((r) => r.data),
  accounts: () => api.get("/api/v1/accounts").then((r) => r.data),
  dashboard: () => api.get("/api/v1/stats/dashboard").then((r) => r.data),

  // 조직 · 사용자 관리 (관리자)
  org: () => api.get("/api/v1/org").then((r) => r.data),
  createDepartment: (body: { name: string; code?: string }) =>
    api.post("/api/v1/departments", body).then((r) => r.data),
  updateDepartment: (id: string, body: { name?: string; code?: string }) =>
    api.patch(`/api/v1/departments/${id}`, body).then((r) => r.data),
  deleteDepartment: (id: string) => api.delete(`/api/v1/departments/${id}`).then((r) => r.data),
  createTeam: (body: { department_id: string; name: string }) =>
    api.post("/api/v1/teams", body).then((r) => r.data),
  updateTeam: (id: string, body: { name: string }) =>
    api.patch(`/api/v1/teams/${id}`, body).then((r) => r.data),
  deleteTeam: (id: string) => api.delete(`/api/v1/teams/${id}`).then((r) => r.data),
  users: () => api.get("/api/v1/users").then((r) => r.data),
  createUser: (body: unknown) => api.post("/api/v1/users", body).then((r) => r.data),
  updateUser: (id: string, body: unknown) =>
    api.patch(`/api/v1/users/${id}`, body).then((r) => r.data),
  reports: () => api.get("/api/v1/expenses/reports").then((r) => r.data),
  report: (id: string) => api.get(`/api/v1/expenses/reports/${id}`).then((r) => r.data),
  createReport: (body: unknown) =>
    api.post("/api/v1/expenses/reports", body).then((r) => r.data),
  updateReport: (id: string, body: unknown) =>
    api.put(`/api/v1/expenses/reports/${id}`, body).then((r) => r.data),
  deleteReport: (id: string) =>
    api.delete(`/api/v1/expenses/reports/${id}`).then((r) => r.data),
  submitReport: (id: string) =>
    api.post(`/api/v1/expenses/reports/${id}/submit`).then((r) => r.data),
  validate: (id: string) =>
    api.get(`/api/v1/expenses/reports/${id}/validate`).then((r) => r.data),
  history: (id: string) =>
    api.get(`/api/v1/expenses/reports/${id}/history`).then((r) => r.data),
  approve: (id: string, comment?: string) =>
    api.post(`/api/v1/approvals/${id}/approve`, { comment }).then((r) => r.data),
  reject: (id: string, comment: string) =>
    api.post(`/api/v1/approvals/${id}/reject`, { comment }).then((r) => r.data),
  review: (id: string, comment?: string) =>
    api.post(`/api/v1/approvals/${id}/review`, { comment }).then((r) => r.data),
  closings: () => api.get("/api/v1/closings").then((r) => r.data),
  close: (period: string) =>
    api.post("/api/v1/closings", { period }).then((r) => r.data),
  downloadUrl: (id: string) => `${API_BASE}/api/v1/closings/${id}/download`,
  receiptsZipUrl: (id: string) => `${API_BASE}/api/v1/closings/${id}/receipts-zip`,
  receiptImageUrl: (itemId: string) => `${API_BASE}/api/v1/receipts/${itemId}/image`,
};

/** 인증 헤더가 필요한 파일을 blob으로 받아 새 탭/다운로드로 연다. */
export async function authedBlob(url: string): Promise<Blob | null> {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${tokenStore.access()}` },
  });
  if (!res.ok) return null;
  return res.blob();
}

export { API_BASE };
