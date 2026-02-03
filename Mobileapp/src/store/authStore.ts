import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

interface User {
  id: string;
  email: string;
  subscription_tier: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: User) => void;
  clearAuth: () => void;
  checkAuth: () => Promise<void>;
}

const API_URL = 'http://localhost:8000'; // Change to your backend URL

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      setAuth: (token: string, user: User) => {
        set({ token, user, isAuthenticated: true });
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      },

      clearAuth: () => {
        set({ token: null, user: null, isAuthenticated: false });
        delete axios.defaults.headers.common['Authorization'];
      },

      checkAuth: async () => {
        const { token } = get();
        if (!token) {
          set({ isAuthenticated: false });
          return;
        }

        try {
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          const response = await axios.get(`${API_URL}/api/auth/me`);
          set({ user: response.data, isAuthenticated: true });
        } catch (error) {
          get().clearAuth();
        }
      },
    }),
    {
      name: 'holomed-auth',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
