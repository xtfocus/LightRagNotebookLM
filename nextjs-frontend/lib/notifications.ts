import { NotificationType } from "@/components/ui/Notification";

// Common notification messages
export const NOTIFICATION_MESSAGES = {
  // Registration
  REGISTRATION_SUCCESS: {
    title: "Welcome to the waitlist!",
    message: "Your account has been created successfully. You've been added to our waitlist.",
    type: "success" as NotificationType,
  },
  REGISTRATION_ERROR: {
    title: "Registration Failed",
    message: "Unable to create your account. Please try again.",
    type: "error" as NotificationType,
  },
  
  // Login
  LOGIN_SUCCESS: {
    title: "Welcome back!",
    message: "You have been successfully logged in.",
    type: "success" as NotificationType,
  },
  LOGIN_ERROR: {
    title: "Login Failed",
    message: "Invalid email or password. Please try again.",
    type: "error" as NotificationType,
  },
  
  // Password Reset
  PASSWORD_RESET_SENT: {
    title: "Reset Email Sent",
    message: "If an account exists with that email, you will receive password reset instructions.",
    type: "info" as NotificationType,
  },
  PASSWORD_RESET_ERROR: {
    title: "Reset Failed",
    message: "Unable to send reset email. Please try again.",
    type: "error" as NotificationType,
  },
  
  // General
  NETWORK_ERROR: {
    title: "Connection Error",
    message: "Unable to connect to the server. Please check your internet connection.",
    type: "error" as NotificationType,
  },
  UNEXPECTED_ERROR: {
    title: "Something went wrong",
    message: "An unexpected error occurred. Please try again later.",
    type: "error" as NotificationType,
  },
  
  // Waitlist specific
  WAITLIST_JOINED: {
    title: "You're on the waitlist!",
    message: "We'll notify you when your account is ready to use.",
    type: "success" as NotificationType,
  },
  WAITLIST_FULL: {
    title: "Waitlist is full",
    message: "Our waitlist is currently at capacity. Please try again later.",
    type: "warning" as NotificationType,
  },
} as const;

// Helper function to get notification config
export function getNotificationConfig(key: keyof typeof NOTIFICATION_MESSAGES) {
  return NOTIFICATION_MESSAGES[key];
}

// Helper function to create custom notifications
export function createNotification(
  type: NotificationType,
  title: string,
  message?: string,
  options?: {
    autoClose?: boolean;
    autoCloseDelay?: number;
  }
) {
  return {
    type,
    title,
    message,
    autoClose: options?.autoClose ?? true,
    autoCloseDelay: options?.autoCloseDelay ?? 5000,
  };
} 