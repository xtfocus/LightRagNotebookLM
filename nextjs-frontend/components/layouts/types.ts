// Define types for better reusability
export interface NavigationItem {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  prefetch?: boolean;
}

export interface BreadcrumbConfig {
  path: string;
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
}

export interface AppLayoutProps {
  children: React.ReactNode;
  navigationItems?: NavigationItem[];
  breadcrumbConfigs?: BreadcrumbConfig[];
  logo?: {
    src: string;
    alt: string;
    width?: number;
    height?: number;
  };
  userMenuItems?: React.ReactNode;
  onLogout?: () => Promise<void>;
  className?: string;
} 