"use client";

import { Loader2 } from "lucide-react";

interface PageLoadingProps {
  message?: string;
  className?: string;
}

export function PageLoading({ message = "Loading...", className = "" }: PageLoadingProps) {
  return (
    <div className={`flex items-center justify-center min-h-[200px] ${className}`}>
      <div className="flex items-center space-x-3">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
        <span className="text-lg text-gray-600 dark:text-gray-400">{message}</span>
      </div>
    </div>
  );
} 