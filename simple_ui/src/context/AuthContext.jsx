import React, { createContext, useContext, useState, useCallback } from 'react';
import { saveToken, logout as logoutApi, getToken } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getToken());

  const login = useCallback((accessToken) => {
    saveToken(accessToken);
    setToken(accessToken);
  }, []);

  const logout = useCallback(() => {
    logoutApi();
    setToken(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, isLoggedIn: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
