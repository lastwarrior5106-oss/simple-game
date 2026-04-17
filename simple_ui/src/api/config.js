export const API_BASE = "http://127.0.0.1:8000";

export const ENDPOINTS = {
  login: `${API_BASE}/auth/login`,
  register: `${API_BASE}/auth/register`,
  chatStream: `${API_BASE}/ai/chat/stream`,
  changeEmail: `${API_BASE}/auth/change-email`,
  changePassword: `${API_BASE}/auth/change-password`,
};
