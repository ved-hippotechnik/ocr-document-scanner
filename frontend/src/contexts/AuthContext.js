import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Set up axios interceptors
  useEffect(() => {
    // Request interceptor to add auth token
    const requestInterceptor = axios.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle token refresh
    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await axios.post(`${API_URL}/api/auth/refresh`, {
                refresh_token: refreshToken
              });
              
              if (response.data.access_token) {
                localStorage.setItem('access_token', response.data.access_token);
                originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
                return axios(originalRequest);
              }
            }
          } catch (refreshError) {
            // Refresh failed, logout user — preserve returnTo path (Q6)
            logout();
            const returnTo = window.location.pathname;
            window.location.href = `/auth/login${returnTo !== '/' ? `?returnTo=${encodeURIComponent(returnTo)}` : ''}`;
          }
        }
        
        return Promise.reject(error);
      }
    );

    // Cleanup
    return () => {
      axios.interceptors.request.eject(requestInterceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  // Proactive token refresh: schedule refresh 5 minutes before JWT expiry
  useEffect(() => {
    if (!isAuthenticated) return;

    let timeoutId;

    const scheduleRefresh = () => {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        // Decode JWT payload (base64 middle segment)
        const parts = token.split('.');
        if (parts.length !== 3) return;

        const payload = JSON.parse(atob(parts[1]));
        const exp = payload.exp;
        if (!exp) return;

        const now = Math.floor(Date.now() / 1000);
        // Refresh 5 minutes (300 seconds) before expiry
        const refreshAt = (exp - 300 - now) * 1000;

        if (refreshAt <= 0) return; // Already past refresh window

        // Q4 — Dispatch session-expiring event 2 minutes before expiry
        const warnAt = (exp - 120 - now) * 1000;
        let warnTimeoutId;
        if (warnAt > 0) {
          warnTimeoutId = setTimeout(() => {
            window.dispatchEvent(new CustomEvent('session-expiring'));
          }, warnAt);
        }

        timeoutId = setTimeout(async () => {
          if (warnTimeoutId) clearTimeout(warnTimeoutId);
          const attemptRefresh = async (retries = 3, backoffMs = 5000) => {
            for (let attempt = 1; attempt <= retries; attempt++) {
              try {
                const refreshToken = localStorage.getItem('refresh_token');
                if (!refreshToken) return false;

                const response = await axios.post(`${API_URL}/api/auth/refresh`, {
                  refresh_token: refreshToken
                });

                if (response.data.access_token) {
                  localStorage.setItem('access_token', response.data.access_token);
                  if (response.data.refresh_token) {
                    localStorage.setItem('refresh_token', response.data.refresh_token);
                  }
                  scheduleRefresh();
                  return true;
                }
              } catch (refreshError) {
                console.debug(`Proactive token refresh attempt ${attempt}/${retries} failed:`, refreshError.message);
                if (attempt < retries) {
                  await new Promise(r => setTimeout(r, backoffMs * attempt));
                }
              }
            }
            return false;
          };
          await attemptRefresh();
        }, refreshAt);
      } catch (decodeError) {
        // Malformed token; skip proactive refresh
        console.debug('Could not decode token for proactive refresh:', decodeError.message);
      }
    };

    scheduleRefresh();

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [isAuthenticated]);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const storedUser = localStorage.getItem('user');
      
      if (token && storedUser) {
        // Verify token is still valid
        const response = await axios.get(`${API_URL}/api/auth/profile`);
        setUser(response.data.user);
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
      // Clear invalid tokens
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API_URL}/api/auth/login`, {
        email,
        password
      });
      
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('refresh_token', response.data.refresh_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        setUser(response.data.user);
        setIsAuthenticated(true);
        
        return { success: true, data: response.data };
      }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API_URL}/api/auth/register`, userData);
      
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('refresh_token', response.data.refresh_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        setUser(response.data.user);
        setIsAuthenticated(true);
        
        return { success: true, data: response.data };
      }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    
    setUser(null);
    setIsAuthenticated(false);
  };

  const updateProfile = async (profileData) => {
    try {
      const response = await axios.put(`${API_URL}/api/auth/profile`, profileData);
      
      if (response.data.user) {
        setUser(response.data.user);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        return { success: true, data: response.data };
      }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Profile update failed' 
      };
    }
  };

  const changePassword = async (currentPassword, newPassword) => {
    try {
      const response = await axios.post(`${API_URL}/api/auth/change-password`, {
        current_password: currentPassword,
        new_password: newPassword
      });
      
      return { success: true, message: response.data.message };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Password change failed' 
      };
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    checkAuth
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;