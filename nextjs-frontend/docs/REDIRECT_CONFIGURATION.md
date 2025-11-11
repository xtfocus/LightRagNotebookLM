# Redirect Configuration

This document explains the environment-based redirect configuration system implemented for the Next.js frontend.

## Overview

The redirect system allows you to configure redirect paths using environment variables, making the application more flexible for different deployment scenarios and configurations.

## Environment Variables

The following environment variables can be set to customize redirect paths:

### `NEXT_PUBLIC_REDIRECT_DASHBOARD`
- **Default**: `/dashboard`
- **Description**: Path to redirect after successful login
- **Usage**: After user authentication succeeds

### `NEXT_PUBLIC_REDIRECT_LOGIN`
- **Default**: `/login`
- **Description**: Path to redirect after logout or authentication failure
- **Usage**: After logout, failed authentication, or middleware redirects

### `NEXT_PUBLIC_REDIRECT_REGISTER_SUCCESS`
- **Default**: `/login`
- **Description**: Path to redirect after successful registration (if needed)
- **Usage**: Currently not used, but available for future registration flows

### `NEXT_PUBLIC_REDIRECT_PASSWORD_RESET`
- **Default**: `/login`
- **Description**: Path to redirect after successful password reset
- **Usage**: After password reset confirmation

## Implementation

### Configuration Utility
The redirect paths are managed through `lib/redirects.ts`, which provides:

- `getRedirectPath(action)`: Get the configured path for a specific action
- `getAllRedirectPaths()`: Get all configured paths for debugging
- `validateRedirectPaths()`: Validate that all paths are properly configured

### Usage in Code
```typescript
import { getRedirectPath } from "@/lib/redirects";

// Instead of hardcoded redirects
redirect("/dashboard");

// Use the configuration utility
redirect(getRedirectPath("DASHBOARD"));
```

## Deployment Examples

### Development Environment
```bash
# Use defaults (no environment variables needed)
npm run dev
```

### Production with Custom Paths
```bash
# Custom redirect paths for production
NEXT_PUBLIC_REDIRECT_DASHBOARD=/app
NEXT_PUBLIC_REDIRECT_LOGIN=/auth/login
NEXT_PUBLIC_REDIRECT_PASSWORD_RESET=/auth/login
```

### Staging Environment
```bash
# Different paths for staging
NEXT_PUBLIC_REDIRECT_DASHBOARD=/staging/dashboard
NEXT_PUBLIC_REDIRECT_LOGIN=/staging/login
```

## Validation

The system includes validation to ensure all redirect paths:
- Start with "/" (absolute paths)
- Are properly configured

You can validate the configuration programmatically:
```typescript
import { validateRedirectPaths } from "@/lib/redirects";

const validation = validateRedirectPaths();
if (!validation.isValid) {
  console.error("Redirect configuration errors:", validation.errors);
}
```

## Benefits

1. **Flexibility**: Easy to change redirects for different environments
2. **Deployment Ready**: Works with different deployment configurations
3. **Maintainability**: Centralized configuration management
4. **Testing**: Easy to test different redirect scenarios
5. **Demo Friendly**: Can customize paths for different demo scenarios

## Migration Notes

- All hardcoded redirects have been replaced with the configuration utility
- Default values maintain backward compatibility
- No breaking changes for existing deployments
- Environment variables are optional and have sensible defaults 