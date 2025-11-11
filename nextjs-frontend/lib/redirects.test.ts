/**
 * Simple test for redirect configuration utility
 * This can be run manually to verify the redirect system works correctly
 */

import { getRedirectPath, getAllRedirectPaths, validateRedirectPaths } from './redirects';

// Test the redirect configuration
console.log('=== Redirect Configuration Test ===');

// Test getting individual paths
console.log('Dashboard redirect:', getRedirectPath('DASHBOARD'));
console.log('Login redirect:', getRedirectPath('LOGIN'));
console.log('Password reset redirect:', getRedirectPath('PASSWORD_RESET_SUCCESS'));

// Test getting all paths
console.log('\nAll redirect paths:', getAllRedirectPaths());

// Test validation
const validation = validateRedirectPaths();
console.log('\nValidation result:', validation);

if (validation.isValid) {
  console.log('✅ All redirect paths are valid');
} else {
  console.log('❌ Redirect path validation failed:');
  validation.errors.forEach(error => console.log(`  - ${error}`));
}

// Test with custom environment variables (if set)
if (process.env.NEXT_PUBLIC_REDIRECT_DASHBOARD) {
  console.log('\nCustom dashboard path detected:', process.env.NEXT_PUBLIC_REDIRECT_DASHBOARD);
}

if (process.env.NEXT_PUBLIC_REDIRECT_LOGIN) {
  console.log('Custom login path detected:', process.env.NEXT_PUBLIC_REDIRECT_LOGIN);
}

console.log('\n=== Test Complete ==='); 