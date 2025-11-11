/**
 * Error message mapping system
 * 
 * This utility translates backend technical error messages into user-friendly
 * frontend messages for better user experience during demos.
 */

export interface ErrorMapping {
  [key: string]: {
    message: string;
    suggestion?: string;
    type: 'error' | 'warning' | 'info';
  };
}

// Comprehensive mapping of backend error messages to user-friendly messages
export const ERROR_MAPPINGS: ErrorMapping = {
  // Login errors
  "Incorrect email or password": {
    message: "The email or password you entered is incorrect.",
    suggestion: "Please check your credentials and try again.",
    type: "error"
  },
  "Inactive user": {
    message: "Your account has been deactivated.",
    suggestion: "Please contact support if you believe this is an error.",
    type: "error"
  },
  "Your account is pending admin approval. Please wait for approval before signing in.": {
    message: "Your account is pending approval.",
    suggestion: "You'll be able to sign in once an administrator approves your account.",
    type: "warning"
  },

  // Registration errors
  "The user with this email already exists in the system": {
    message: "An account with this email already exists.",
    suggestion: "Try signing in instead, or use a different email address.",
    type: "error"
  },
  "The user with this email already exists in the system.": {
    message: "An account with this email already exists.",
    suggestion: "Try signing in instead, or use a different email address.",
    type: "error"
  },

  // Password reset errors
  "Invalid token": {
    message: "The password reset link is invalid or has expired.",
    suggestion: "Please request a new password reset link.",
    type: "error"
  },
  "The user with this email does not exist in the system.": {
    message: "No account found with this email address.",
    suggestion: "Please check the email address or create a new account.",
    type: "error"
  },

  // User management errors
  "The user doesn't have enough privileges": {
    message: "You don't have permission to perform this action.",
    suggestion: "Please contact an administrator if you need access.",
    type: "error"
  },
  "The user with this id does not exist in the system": {
    message: "The requested user could not be found.",
    suggestion: "The user may have been deleted or the link may be outdated.",
    type: "error"
  },
  "User with this email already exists": {
    message: "An account with this email already exists.",
    suggestion: "Please use a different email address or contact support.",
    type: "error"
  },
  "User not found": {
    message: "The requested user could not be found.",
    suggestion: "The user may have been deleted or the link may be outdated.",
    type: "error"
  },
  "Super users are not allowed to delete themselves": {
    message: "Administrators cannot delete their own accounts.",
    suggestion: "Please contact another administrator for assistance.",
    type: "warning"
  },

  // Network and general errors
  "Network error": {
    message: "Unable to connect to the server.",
    suggestion: "Please check your internet connection and try again.",
    type: "error"
  },
  "Failed to fetch waitlist users": {
    message: "Unable to load the user waitlist.",
    suggestion: "Please refresh the page and try again.",
    type: "error"
  },
  "Failed to approve user": {
    message: "Unable to approve the user at this time.",
    suggestion: "Please try again or contact support if the issue persists.",
    type: "error"
  },
  "Failed to reject user": {
    message: "Unable to reject the user at this time.",
    suggestion: "Please try again or contact support if the issue persists.",
    type: "error"
  }
};

/**
 * Get a user-friendly error message from a backend error
 * @param error - The error object or message from the backend
 * @returns User-friendly error message with optional suggestion
 */
export function getUserFriendlyError(error: any): {
  message: string;
  suggestion?: string;
  type: 'error' | 'warning' | 'info';
} {
  // Extract the error message
  let errorMessage = "An unexpected error occurred. Please try again later.";
  
  if (typeof error === "string") {
    errorMessage = error;
  } else if (error?.detail) {
    errorMessage = error.detail;
  } else if (error?.message) {
    errorMessage = error.message;
  }

  // Look for an exact match in our mappings
  const mapping = ERROR_MAPPINGS[errorMessage];
  if (mapping) {
    return mapping;
  }

  // If no mapping found, return a generic error message
  return {
    message: "Something went wrong. Please try again.",
    suggestion: "If the problem persists, please contact support.",
    type: "error"
  };
}

/**
 * Get just the error message without suggestion
 * @param error - The error object or message from the backend
 * @returns User-friendly error message
 */
export function getErrorMessage(error: any): string {
  return getUserFriendlyError(error).message;
}

/**
 * Get error message with suggestion
 * @param error - The error object or message from the backend
 * @returns Formatted error message with suggestion
 */
export function getErrorMessageWithSuggestion(error: any): string {
  const { message, suggestion } = getUserFriendlyError(error);
  if (suggestion) {
    return `${message} ${suggestion}`;
  }
  return message;
}

/**
 * Get all available error mappings for debugging
 * @returns Object containing all error mappings
 */
export function getAllErrorMappings(): ErrorMapping {
  return { ...ERROR_MAPPINGS };
}

/**
 * Add a custom error mapping
 * @param backendMessage - The exact backend error message
 * @param userMessage - The user-friendly message
 * @param suggestion - Optional suggestion for the user
 * @param type - The type of error (error, warning, info)
 */
export function addErrorMapping(
  backendMessage: string,
  userMessage: string,
  suggestion?: string,
  type: 'error' | 'warning' | 'info' = 'error'
): void {
  ERROR_MAPPINGS[backendMessage] = {
    message: userMessage,
    suggestion,
    type
  };
} 