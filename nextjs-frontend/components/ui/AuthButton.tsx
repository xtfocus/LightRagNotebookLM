'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { User, LogOut, Settings } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { UserAvatar } from '@/components/ui/UserAvatar';

interface AuthButtonProps {
  className?: string;
}

export function AuthButton({ className = '' }: AuthButtonProps) {
  const { user, isAuthenticated, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  // Show Sign In button when not authenticated
  if (!isAuthenticated) {
    return (
      <div className={`flex gap-3 ${className}`}>
        <Link href="/login">
          <Button variant="ghost" className="text-base">
            Sign In
          </Button>
        </Link>
        <Link href="/register">
          <Button className="text-base">
            Sign Up
          </Button>
        </Link>
      </div>
    );
  }

  // Show user dropdown when authenticated
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className={`h-12 w-12 rounded-full p-0 hover:bg-gray-100 dark:hover:bg-gray-800 ${className}`}
        >
          <UserAvatar user={user!} size="md" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="px-4 py-3">
          <div className="flex items-center gap-3">
            <UserAvatar user={user!} size="md" />
            <div className="flex flex-col">
              <span className="text-base font-medium">{user?.full_name || 'User'}</span>
              <span className="text-sm text-muted-foreground">{user?.email}</span>
            </div>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/dashboard" className="flex items-center gap-3 px-4 py-2">
            <User className="h-5 w-5" />
            <span className="text-base">Dashboard</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/profile" className="flex items-center gap-3 px-4 py-2">
            <Settings className="h-5 w-5" />
            <span className="text-base">Profile</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem 
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-2 text-red-600 focus:text-red-600"
        >
          <LogOut className="h-5 w-5" />
          <span className="text-base">Logout</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
} 