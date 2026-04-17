import { ENDPOINTS } from './config';

/**
 * Login - OAuth2PasswordRequestForm formatında gönderir (FastAPI uyumlu)
 */
export async function loginApi(email, password) {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const res = await fetch(ENDPOINTS.login, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData.toString(),
  });

  let data = null;

  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) throw new Error(data?.detail || 'Giriş başarısız');
  return data;
}

/**
 * Register - JSON body ile email + password
 */
export async function registerApi(email, password) {
  const res = await fetch(ENDPOINTS.register, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  let data = null;

  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) throw new Error(data?.detail || 'Kayıt başarısız');
  return data;
}

/**
 * Token'ı localStorage'a kaydet
 */
export function saveToken(token) {
  localStorage.setItem('access_token', token);
}

/**
 * Token'ı localStorage'dan al
 */
export function getToken() {
  return localStorage.getItem('access_token') || '';
}

/**
 * Logout - token'ı sil
 */
export function logout() {
  localStorage.removeItem('access_token');
}
