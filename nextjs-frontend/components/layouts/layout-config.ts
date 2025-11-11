import { LayoutDashboard, Package, MessageCircle, Shield, Users2, BookOpen, Briefcase } from "lucide-react";
import { NavigationItem, BreadcrumbConfig } from "./types";

// Single source of truth for routes
const ROUTES = {
  dashboard: { path: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  customers: { path: "/customers", icon: Users2, label: "Customers" },
  items: { path: "/items", icon: Package, label: "Items" },
  aguichat: { path: "/aguichat", icon: MessageCircle, label: "AG-UI Chat" },
  notebooks: { path: "/notebooks", icon: BookOpen, label: "Notebooks" },
  sources: { path: "/sources", icon: Briefcase, label: "Source Manager" },
  admin: { path: "/admin", icon: Shield, label: "Admin" },
} as const;

// Generate navigation items from single source
export const currentAppNavigation: NavigationItem[] = Object.values(ROUTES).map(route => ({
  href: route.path,
  icon: route.icon,
  label: route.label,
  prefetch: true,
}));

// Generate breadcrumb configuration from single source
export const currentAppBreadcrumbs: BreadcrumbConfig[] = Object.values(ROUTES).map(route => ({
  path: route.path,
  title: route.label,
  icon: route.icon,
  href: route.path,
}));

// Add sub-routes that aren't in main navigation
export const currentAppBreadcrumbsWithSubRoutes: BreadcrumbConfig[] = [
  ...currentAppBreadcrumbs,
  {
    path: "/items/add-item",
    title: "Add Item",
    icon: Package,
    href: "/items/add-item",
  },
];

// Logo configuration
export const logoConfig = {
  src: "/images/home.png",
  alt: "HomePage",
  width: 64,
  height: 64,
}; 