"use client";

import { AppLayout } from "@/components/layouts/AppLayout";
import { currentAppNavigation, currentAppBreadcrumbsWithSubRoutes, logoConfig } from "@/components/layouts/layout-config";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/contexts/AuthContext";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { logout } = useAuth();

  // Handle logout with proper error handling
  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      // Log unexpected errors
      console.error('Logout error:', error);
    }
  };

  return (
    <ProtectedRoute>
      <AppLayout
        navigationItems={currentAppNavigation}
        breadcrumbConfigs={currentAppBreadcrumbsWithSubRoutes}
        logo={logoConfig}
        onLogout={handleLogout}
      >
        {children}
      </AppLayout>
    </ProtectedRoute>
  );
} 