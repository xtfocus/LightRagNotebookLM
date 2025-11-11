import { useMemo } from 'react';
import { DateFormattingOptions, UseDateFormattingReturn } from '@/types/notebook';

export function useDateFormatting(): UseDateFormattingReturn {
  const formatDate = useMemo(() => {
    return (dateString: string, options?: DateFormattingOptions) => {
      const date = new Date(dateString);
      
      // Default options for notebook dates
      const defaultOptions: DateFormattingOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      };
      
      const finalOptions = { ...defaultOptions, ...options };
      
      return date.toLocaleDateString('en-US', finalOptions);
    };
  }, []);

  const formatDateTime = useMemo(() => {
    return (dateString: string, options?: DateFormattingOptions) => {
      const date = new Date(dateString);
      
      // Default options for full date/time
      const defaultOptions: DateFormattingOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      };
      
      const finalOptions = { ...defaultOptions, ...options };
      
      return date.toLocaleDateString('en-US', finalOptions);
    };
  }, []);

  const formatRelativeTime = useMemo(() => {
    return (dateString: string) => {
      const date = new Date(dateString);
      const now = new Date();
      const diffInMs = now.getTime() - date.getTime();
      const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
      const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
      const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

      if (diffInMinutes < 1) {
        return 'Just now';
      } else if (diffInMinutes < 60) {
        return `${diffInMinutes}m ago`;
      } else if (diffInHours < 24) {
        return `${diffInHours}h ago`;
      } else if (diffInDays < 7) {
        return `${diffInDays}d ago`;
      } else {
        return formatDate(dateString);
      }
    };
  }, [formatDate]);

  return {
    formatDate,
    formatDateTime,
    formatRelativeTime,
  };
} 