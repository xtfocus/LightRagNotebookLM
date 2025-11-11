import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

interface UseAuthRedirectOptions {
  redirectTo?: string;
  requireAuth?: boolean;
}

export function useAuthRedirect({ 
  redirectTo = "/dashboard", 
  requireAuth = true 
}: UseAuthRedirectOptions = {}) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (requireAuth && !isAuthenticated) {
        // Redirect to login if authentication is required but user is not authenticated
        router.push("/login");
      } else if (!requireAuth && isAuthenticated) {
        // Redirect to dashboard if user is authenticated but shouldn't be on this page
        router.push(redirectTo);
      }
    }
  }, [isAuthenticated, loading, router, redirectTo, requireAuth]);

  return { isAuthenticated, loading };
} 