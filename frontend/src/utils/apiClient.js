/**
 * Centralized axios instance for all API calls.
 *
 * AuthContext.js already sets up request/response interceptors on the
 * global axios instance (token injection, 401 refresh). This module
 * re-exports that same instance so every part of the app goes through
 * the same pipeline.
 *
 * Usage:
 *   import api from '../utils/apiClient';
 *   const { data } = await api.get('/api/v3/developer/keys');
 */
import axios from 'axios';
import config from '../config';

const api = axios.create({
  baseURL: config.API_URL,
  timeout: config.request.timeout,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — attach JWT token
api.interceptors.request.use((req) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    req.headers.Authorization = `Bearer ${token}`;
  }
  return req;
});

// Response interceptor — attempt silent token refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${config.API_URL}/api/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', data.access_token);
          original.headers.Authorization = `Bearer ${data.access_token}`;
          return api(original);
        } catch {
          // Refresh failed — let caller handle 401
        }
      }
    }
    return Promise.reject(error);
  },
);

export default api;
