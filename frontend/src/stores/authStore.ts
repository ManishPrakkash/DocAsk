import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthState, User } from '../types';
import { authAPI, handleAPIError } from '../lib/api';
import toast from 'react-hot-toast';

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        
        try {
          const tokenResponse = await authAPI.login({ email, password });
          const { access_token } = tokenResponse;
          
          // Store token in localStorage and state
          localStorage.setItem('auth_token', access_token);
          
          // Get user profile
          const user = await authAPI.getProfile();
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          });
          
          toast.success('Login successful!');
        } catch (error) {
          const errorMessage = handleAPIError(error);
          toast.error(errorMessage);
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (email: string, password: string) => {
        set({ isLoading: true });
        
        try {
          await authAPI.register({ email, password });
          
          // Auto-login after successful registration
          const tokenResponse = await authAPI.login({ email, password });
          const { access_token } = tokenResponse;
          
          // Store token in localStorage and state
          localStorage.setItem('auth_token', access_token);
          
          // Get user profile
          const user = await authAPI.getProfile();
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          });
          
          toast.success('Registration successful!');
        } catch (error) {
          const errorMessage = handleAPIError(error);
          toast.error(errorMessage);
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        try {
          authAPI.logout().catch(() => {
            // Ignore logout API errors - proceed with client-side logout
          });
        } finally {
          localStorage.removeItem('auth_token');
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
          toast.success('Logged out successfully');
        }
      },

      checkAuth: async () => {
        const token = localStorage.getItem('auth_token');
        
        if (!token) {
          set({ isAuthenticated: false, user: null, token: null });
          return;
        }
        
        try {
          const user = await authAPI.getProfile();
          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          // Token is invalid, clear it
          localStorage.removeItem('auth_token');
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);