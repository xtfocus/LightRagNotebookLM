/**
 * Centralized error handling utilities for consistent error management
 */

export interface ApiError {
  message: string;
  detail?: string;
  status?: number;
}

export interface ErrorResult {
  message: string;
  type: 'api' | 'validation' | 'network' | 'unknown';
}

// Re-export the existing notification types for consistency
export type { NotificationType } from '@/components/ui/Notification';

/**
 * Type guard to check if an error is an API error
 */
export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as any).message === 'string'
  );
}

/**
 * Convert any error to a user-friendly message
 */
export function handleApiError(error: unknown): string {
  if (isApiError(error)) {
    return error.detail || error.message;
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  return 'An unexpected error occurred. Please try again.';
}

/**
 * Convert any error to a structured ErrorResult
 */
export function createErrorResult(error: unknown): ErrorResult {
  if (isApiError(error)) {
    return {
      message: error.detail || error.message,
      type: 'api'
    };
  }
  
  if (error instanceof Error) {
    return {
      message: error.message,
      type: error.name === 'ValidationError' ? 'validation' : 'unknown'
    };
  }
  
  if (typeof error === 'string') {
    return {
      message: error,
      type: 'unknown'
    };
  }
  
  return {
    message: 'An unexpected error occurred. Please try again.',
    type: 'unknown'
  };
}

/**
 * Centralized logging for errors
 */
export function logError(error: unknown, context: string): void {
  const errorResult = createErrorResult(error);
  
  console.error(`[${context}] Error:`, {
    message: errorResult.message,
    type: errorResult.type,
    originalError: error,
    timestamp: new Date().toISOString()
  });
}

/**
 * Check if an error is a Next.js redirect (which is expected behavior)
 */
export function isNextRedirectError(error: unknown): boolean {
  return (
    typeof error === 'object' &&
    error !== null &&
    'digest' in error &&
    typeof (error as any).digest === 'string' &&
    (error as any).digest.startsWith('NEXT_REDIRECT')
  );
}

/**
 * Show error notification using the existing notification system
 */
export function showErrorNotification(
  addNotification: (notification: { type: 'error' | 'warning' | 'info' | 'success'; title: string; message?: string }) => void,
  error: unknown,
  context: string = 'Operation'
): void {
  const errorMessage = handleApiError(error);
  logError(error, context);
  
  addNotification({
    type: 'error',
    title: `${context} Failed`,
    message: errorMessage,
  });
}

/**
 * Show success notification using the existing notification system
 */
export function showSuccessNotification(
  addNotification: (notification: { type: 'error' | 'warning' | 'info' | 'success'; title: string; message?: string }) => void,
  title: string,
  message?: string
): void {
  addNotification({
    type: 'success',
    title,
    message,
  });
} 