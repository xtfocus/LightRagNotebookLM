"use client";

import { useFormStatus } from "react-dom";
import { Loader2 } from "lucide-react";

interface FormLoadingOverlayProps {
  children: React.ReactNode;
  className?: string;
}

export function FormLoadingOverlay({ children, className = "" }: FormLoadingOverlayProps) {
  const { pending } = useFormStatus();

  if (!pending) {
    return <>{children}</>;
  }

  return (
    <div className={`relative ${className}`}>
      {children}
      <div className="absolute inset-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-lg flex items-center justify-center z-10">
        <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-300">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm font-medium">Processing...</span>
        </div>
      </div>
    </div>
  );
} 