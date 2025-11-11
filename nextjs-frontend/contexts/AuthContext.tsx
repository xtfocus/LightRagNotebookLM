'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { logout as logoutAction } from '@/components/actions/logout-action';

interface User {
  id: string;
  email: string;
  is_superuser: boolean;
  full_name?: string | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<boolean>;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const checkAuth = useCallback(async (): Promise<boolean> => {
    try {
      // Get the access token from cookies
      const token = document.cookie
        .split('; ')
        .find(row => row.startsWith('accessToken='))
        ?.split('=')[1];

      if (!token) {
        setUser(null);
        return false;
      }

      const response = await fetch("/api/users/me", {
        headers: {
          "Content-Type": "application/json",
          authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        return true;
      } else {
        setUser(null);
        return false;
      }
    } catch (error) {
      console.error("Error checking authentication:", error);
      setUser(null);
      return false;
    }
  }, []);

  const refreshAuth = useCallback(async (): Promise<void> => {
    setLoading(true);
    await checkAuth();
    setLoading(false);
  }, [checkAuth]);

  const login = useCallback((token: string) => {
    // Set the token in cookies
    document.cookie = `accessToken=${token}; path=/; max-age=86400; secure; samesite=lax`;
    // Check auth to get user data
    checkAuth();
  }, [checkAuth]);

  const logout = useCallback(async (): Promise<void> => {
    try {
      // Call server action to clear cookie
      await logoutAction();
      
      // Clear client-side state
      setUser(null);
      
      // Redirect to login
      router.push('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Fallback: clear client-side state and redirect
      setUser(null);
      router.push('/login');
    }
  }, [router]);

  useEffect(() => {
    checkAuth().finally(() => setLoading(false));
  }, [checkAuth]);

  // Remove the window focus listener to prevent excessive calls

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
    checkAuth,
    refreshAuth,
  };

  return (
    <AuthContext.Provider value={value}>
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