/* eslint-disable react-refresh/only-export-components */
// context/auth-context.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// Create Axios instance
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 10000,
});

// Add request interceptor to include token
api.interceptors.request.use(
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

// Add response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't tried refreshing yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post('http://127.0.0.1:8000/auth/token/refresh/', {
            refresh: refreshToken,
          });

          const { access, refresh } = response.data;

          // Update tokens in localStorage
          localStorage.setItem('access_token', access);
          if (refresh) {
            localStorage.setItem('refresh_token', refresh);
          }

          // Update the authorization header
          originalRequest.headers.Authorization = `Bearer ${access}`;

          // Retry the original request
          return api(originalRequest);
        }
      } catch (refreshError) {
        // If refresh fails, logout user
        console.error('Token refresh failed:', refreshError);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is already logged in on mount
  useEffect(() => {
    const checkAuthStatus = async () => {
      const token = localStorage.getItem('access_token');
      const storedUser = localStorage.getItem('user');

      if (token && storedUser) {
        try {
          // Parse stored user data
          const userData = JSON.parse(storedUser);
          
          // Try to verify token by making a simple authenticated request
          // Using profile endpoint as verification
          try {
            const response = await api.get('/profile/');
            // If request succeeds, token is valid
            setUser(response.data);
            // Update stored user data with fresh data
            localStorage.setItem('user', JSON.stringify(response.data));
          } catch (error) {
            // If profile fetch fails but we have stored user data, use it anyway
            // The interceptor will handle token refresh if needed
            if (error.response?.status === 401) {
              // Token is invalid, clear everything
              logout();
            } else {
              // Other error (network, etc), use cached user data
              setUser(userData);
            }
          }
        } catch (error) {
          console.error('Auth check failed:', error);
          // Clear invalid data
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          setUser(null);
        }
      }
      setLoading(false);
    };

    checkAuthStatus();
  }, []);

  const login = async (work_mail_address, password) => {
    try {
      const response = await api.post('/auth/login/', {
        work_mail_address,
        password,
      });

      const { token, status, ...userData } = response.data;

      // Check if user status is pending or rejected
      if (status === 'pending') {
        return {
          success: true,
          status: 'pending',
          message: 'Your account is pending approval'
        };
      }

      if (status === 'rejected') {
        return {
          success: true,
          status: 'rejected',
          message: 'Your account has been rejected'
        };
      }

      // Only store tokens and proceed if status is approved
      if (status === 'approved') {
        // Store tokens
        localStorage.setItem('access_token', token.access);
        localStorage.setItem('refresh_token', token.refresh);
        localStorage.setItem('user', JSON.stringify({ ...userData, status }));

        // Set user in state
        setUser({ ...userData, status });

        return {
          success: true,
          status: 'approved',
          message: 'Login successful'
        };
      }

      // Default case - unknown status
      throw new Error('Unknown account status');

    } catch (error) {
      console.error('Login error:', error);
      
      // Handle specific error messages from backend
      if (error.response) {
        const { data } = error.response;
        if (data.error) {
          throw new Error(data.error);
        }
        if (data.detail) {
          throw new Error(data.detail);
        }
      }
      
      throw new Error('Login failed. Please check your credentials and try again.');
    }
  };

  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        await api.post('/auth/logout/', {
          refresh_token: refreshToken,
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setUser(null);
      // Only redirect if not already on login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
  };

  const updateProfile = async (userData) => {
    try {
      const response = await api.put('/profile/update/', userData);
      const updatedUser = { ...user, ...response.data.user };
      setUser(updatedUser);
      localStorage.setItem('user', JSON.stringify(updatedUser));
      return updatedUser;
    } catch (error) {
      console.error('Update profile error:', error);
      throw error;
    }
  };

  const changePassword = async (currentPassword, newPassword, confirmPassword) => {
    try {
      await api.put('/profile/change-password/', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      return true;
    } catch (error) {
      console.error('Change password error:', error);
      throw error;
    }
  };

  const requestPasswordReset = async (work_mail_address) => {
    try {
      await api.post('/auth/password-reset/request-otp/', {
        work_mail_address,
      });
      return true;
    } catch (error) {
      console.error('Password reset request error:', error);
      throw error;
    }
  };

  const resetPassword = async (work_mail_address, otp, newPassword, confirmPassword) => {
    try {
      await api.post('/auth/password-reset/confirm/', {
        work_mail_address,
        otp,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      return true;
    } catch (error) {
      console.error('Password reset error:', error);
      throw error;
    }
  };

  const getCurrentUser = async () => {
    try {
      const response = await api.get('/profile/');
      setUser(response.data);
      localStorage.setItem('user', JSON.stringify(response.data));
      return response.data;
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  };

  // Department management functions
  const createDepartment = async (departmentData) => {
    try {
      const response = await api.post('/departments/create/', departmentData);
      return response.data;
    } catch (error) {
      console.error('Create department error:', error);
      throw error;
    }
  };

  const updateDepartment = async (departmentId, departmentData) => {
    try {
      const response = await api.put(`/departments/${departmentId}/update/`, departmentData);
      return response.data;
    } catch (error) {
      console.error('Update department error:', error);
      throw error;
    }
  };

  const deleteDepartment = async (departmentId) => {
    try {
      const response = await api.delete(`/departments/${departmentId}/delete/`);
      return response.data;
    } catch (error) {
      console.error('Delete department error:', error);
      throw error;
    }
  };

  const getDepartments = async (params = {}) => {
    try {
      const response = await api.get('/departments/all/', { params });
      return response.data;
    } catch (error) {
      console.error('Get departments error:', error);
      throw error;
    }
  };

  const getDepartmentById = async (departmentId) => {
    try {
      const response = await api.get(`/departments/${departmentId}/`);
      return response.data;
    } catch (error) {
      console.error('Get department by ID error:', error);
      throw error;
    }
  };

  const getMyDepartments = async () => {
    try {
      const response = await api.get('/departments/my-departments/');
      return response.data;
    } catch (error) {
      console.error('Get my departments error:', error);
      throw error;
    }
  };

  // Show loading screen while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading...</p>
          <p className="text-slate-500 text-sm mt-2">Please wait</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        logout,
        updateProfile,
        changePassword,
        requestPasswordReset,
        resetPassword,
        getCurrentUser,
        createDepartment,
        updateDepartment,
        deleteDepartment,
        getDepartmentById,
        getMyDepartments,
        getDepartments,
        api,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export { api };