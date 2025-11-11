"use client";

import { useEffect, useState } from "react";
import { CheckCircle, XCircle, AlertCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type NotificationType = "success" | "error" | "warning" | "info";

interface NotificationProps {
  type: NotificationType;
  title: string;
  message?: string;
  onClose?: () => void;
  autoClose?: boolean;
  autoCloseDelay?: number;
  className?: string;
}

const notificationStyles = {
  success: {
    icon: CheckCircle,
    className: "border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400",
  },
  error: {
    icon: XCircle,
    className: "border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400",
  },
  warning: {
    icon: AlertCircle,
    className: "border-yellow-200 bg-yellow-50 text-yellow-800 dark:border-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400",
  },
  info: {
    icon: Info,
    className: "border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-400",
  },
};

export function Notification({
  type,
  title,
  message,
  onClose,
  autoClose = true,
  autoCloseDelay = 5000,
  className,
}: NotificationProps) {
  const [isVisible, setIsVisible] = useState(true);
  const style = notificationStyles[type];
  const Icon = style.icon;

  useEffect(() => {
    if (autoClose && onClose) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(onClose, 300); // Allow animation to complete
      }, autoCloseDelay);

      return () => clearTimeout(timer);
    }
  }, [autoClose, autoCloseDelay, onClose]);

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className={cn(
        "flex items-start gap-4 p-6 border rounded-lg shadow-sm transition-all duration-300 ease-in-out",
        style.className,
        className
      )}
    >
      <Icon className="h-6 w-6 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <h3 className="font-medium text-base">{title}</h3>
        {message && (
          <p className="mt-2 text-base opacity-90">{message}</p>
        )}
      </div>
      {onClose && (
        <button
          onClick={() => {
            setIsVisible(false);
            setTimeout(onClose, 300);
          }}
          className="flex-shrink-0 p-2 hover:bg-black/10 dark:hover:bg-white/10 rounded transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
      )}
    </div>
  );
}

// Toast-style notification for global use
export function ToastNotification({
  type,
  title,
  message,
  onClose,
  autoClose = true,
  autoCloseDelay = 5000,
}: Omit<NotificationProps, "className">) {
  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm w-full">
      <Notification
        type={type}
        title={title}
        message={message}
        onClose={onClose}
        autoClose={autoClose}
        autoCloseDelay={autoCloseDelay}
        className="shadow-lg"
      />
    </div>
  );
} 