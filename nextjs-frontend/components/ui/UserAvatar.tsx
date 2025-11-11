import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface User {
  id: string;
  email: string;
  is_superuser: boolean;
  full_name?: string | null;
}

interface UserAvatarProps {
  user: User;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function UserAvatar({ user, size = 'md', className = "" }: UserAvatarProps) {
  const getUserInitial = () => {
    if (!user?.full_name) return user?.email?.charAt(0).toUpperCase() || 'U';
    return user.full_name.charAt(0).toUpperCase();
  };

  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12',
  };

  const textSizes = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  };

  return (
    <Avatar className={`${sizeClasses[size]} ${className}`}>
      <AvatarFallback className={`bg-blue-500 text-white font-semibold ${textSizes[size]}`}>
        {getUserInitial()}
      </AvatarFallback>
    </Avatar>
  );
} 