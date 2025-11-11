/**
 * Redirect path configuration utility
 * 
 * This utility provides centralized management of redirect paths with environment
 * variable support for deployment flexibility.
 */

// Environment variables for redirect paths with sensible defaults
const REDIRECT_PATHS = {
  // After successful login
  DASHBOARD: process.env.NEXT_PUBLIC_REDIRECT_DASHBOARD || "/dashboard",
  
  // After logout or authentication failure
  LOGIN: process.env.NEXT_PUBLIC_REDIRECT_LOGIN || "/login",
  
  // After successful registration (if needed)
  REGISTER_SUCCESS: process.env.NEXT_PUBLIC_REDIRECT_REGISTER_SUCCESS || "/login",
  
  // After password reset
  PASSWORD_RESET_SUCCESS: process.env.NEXT_PUBLIC_REDIRECT_PASSWORD_RESET || "/login",
  
  // After notebook creation
  NOTEBOOKS: process.env.NEXT_PUBLIC_REDIRECT_NOTEBOOKS || "/notebooks",
} as const;

/**
 * Get redirect path for a specific action
 * @param action - The action type that needs a redirect
 * @returns The configured redirect path
 */
export function getRedirectPath(action: keyof typeof REDIRECT_PATHS): string {
  return REDIRECT_PATHS[action];
}

/**
 * Get all redirect paths for debugging or configuration display
 * @returns Object containing all redirect paths
 */
export function getAllRedirectPaths(): typeof REDIRECT_PATHS {
  return { ...REDIRECT_PATHS };
}

/**
 * Validate that all redirect paths are properly configured
 * @returns Object with validation results
 */
export function validateRedirectPaths(): {
  isValid: boolean;
  errors: string[];
  paths: typeof REDIRECT_PATHS;
} {
  const errors: string[] = [];
  
  // Check that all paths start with "/"
  Object.entries(REDIRECT_PATHS).forEach(([key, path]) => {
    if (!path.startsWith("/")) {
      errors.push(`${key} redirect path must start with "/": ${path}`);
    }
  });
  
  return {
    isValid: errors.length === 0,
    errors,
    paths: REDIRECT_PATHS,
  };
} 