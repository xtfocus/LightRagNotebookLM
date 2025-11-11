"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { useAuth } from "@/contexts/AuthContext";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { User, LogOut, User as UserIcon } from "lucide-react";
import { AppLayoutProps, NavigationItem } from "./types";

export function AppLayout({
  children,
  navigationItems = [],
  breadcrumbConfigs = [],
  logo,
  userMenuItems,
  onLogout,
  className = "",
}: AppLayoutProps) {
  const pathname = usePathname();
  const { user, loading } = useAuth();

  // Filter navigation items based on user role
  const filteredNavigationItems = navigationItems.filter(item => {
    // If the item has an admin route, only show it to superusers
    if (item.href === "/admin") {
      return user?.is_superuser === true;
    }
    // Show all other items to everyone
    return true;
  });

  // Filter breadcrumb configs based on user role
  const filteredBreadcrumbConfigs = breadcrumbConfigs.filter(config => {
    // If the config has an admin route, only show it to superusers
    if (config.path === "/admin" || config.href === "/admin") {
      return user?.is_superuser === true;
    }
    // Show all other configs to everyone
    return true;
  });

  // Get breadcrumb info for current path
  const getBreadcrumbInfo = () => {
    const currentConfig = filteredBreadcrumbConfigs.find(config => 
      config.path === pathname || config.href === pathname
    );

    if (currentConfig) {
      return {
        href: currentConfig.href || currentConfig.path,
        title: currentConfig.title,
        icon: currentConfig.icon,
      };
    }

    // Fallback for unknown routes
    return {
      href: pathname,
      title: pathname.split('/').pop() || 'Page',
      icon: () => <span>📄</span>,
    };
  };

  const breadcrumbInfo = getBreadcrumbInfo();
  const IconComponent = breadcrumbInfo.icon;
  const isSubRoute = pathname.split('/').length > 2;
  const parentRoute = isSubRoute ? breadcrumbInfo.href.split('/').slice(0, -1).join('/') : null;

  // Hide breadcrumb for notebook workspace pages
  const shouldShowBreadcrumb = !pathname.startsWith('/notebooks/') || pathname === '/notebooks';

  // Get first letter of user email for avatar
  const getUserInitial = () => {
    if (!user?.email) return "U";
    return user.email.charAt(0).toUpperCase();
  };

  return (
    <div className={`flex min-h-screen ${className}`}>
      <aside className="fixed inset-y-0 left-0 z-10 w-16 flex flex-col border-r bg-background p-4">
        <div className="flex flex-col items-center gap-8">
          {logo && (
            <Link
              href="/"
              className="flex items-center justify-center rounded-full"
            >
              <Image
                src={logo.src}
                alt={logo.alt}
                width={logo.width || 64}
                height={logo.height || 64}
                className="object-cover transition-transform duration-200 hover:scale-105"
              />
            </Link>
          )}
          
          {/* Only show navigation items after user data is loaded */}
          {!loading && filteredNavigationItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground"
              prefetch={item.prefetch}
            >
              <item.icon className="h-5 w-5" />
            </Link>
          ))}
        </div>
      </aside>
      
      <main className="ml-16 w-full p-8 bg-muted/40">
        <header className="flex justify-between items-center mb-6">
          <div className="flex-1">
            {shouldShowBreadcrumb && (
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link href="/" className="flex items-center gap-2" prefetch={true}>
                    <span>Home</span>
                  </Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator>/</BreadcrumbSeparator>
              {parentRoute && (
                <>
                  <BreadcrumbItem>
                    <BreadcrumbLink asChild>
                      <Link href={parentRoute} className="flex items-center gap-2" prefetch={true}>
                        <span>Parent</span>
                      </Link>
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator>/</BreadcrumbSeparator>
                </>
              )}
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link href={breadcrumbInfo.href} className="flex items-center gap-2" prefetch={true}>
                    <IconComponent className="h-5 w-5" />
                    <span className="text-base">{breadcrumbInfo.title}</span>
                  </Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
            )}
          </div>
          
          <div className="relative flex-shrink-0">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-300 hover:bg-gray-400 transition-colors">
                  <Avatar>
                    <AvatarFallback className="bg-gray-300 text-gray-700 font-semibold">
                      {getUserInitial()}
                    </AvatarFallback>
                  </Avatar>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" side="bottom" className="w-64">
                {user && (
                  <>
                    <DropdownMenuLabel className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <Avatar className="h-10 w-10">
                          <AvatarFallback className="bg-gray-300 text-gray-700 font-semibold text-base">
                            {getUserInitial()}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col">
                          <span className="text-base font-medium">{user.full_name || 'User'}</span>
                          <span className="text-sm text-muted-foreground">{user.email}</span>
                        </div>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem asChild>
                      <Link href="/profile" className="flex items-center gap-3 px-3 py-2">
                        <UserIcon className="h-5 w-5" />
                        <span className="text-base">Profile</span>
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                  </>
                )}
                {userMenuItems}
                {onLogout && (
                  <DropdownMenuItem asChild>
                    <button
                      onClick={onLogout}
                      className="flex items-center gap-3 px-3 py-2 w-full text-left"
                    >
                      <LogOut className="h-5 w-5" />
                      <span className="text-base">Logout</span>
                    </button>
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>
        <section className="grid gap-6">{children}</section>
      </main>
    </div>
  );
} 