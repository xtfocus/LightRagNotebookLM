import { cookies } from 'next/headers';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { z } from 'zod';

// Types for server action utilities
export interface ServerActionConfig {
  revalidatePaths?: string[];
  redirectPath?: string;
  successMessage?: string;
  errorContext?: string;
}

export interface ApiCallOptions {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  endpoint: string;
  data?: any;
  config?: ServerActionConfig;
}

// Utility to extract auth token from cookies
export async function getAuthToken(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get('accessToken')?.value || null;
}

// Utility to create API headers with auth
export async function createApiHeaders(): Promise<HeadersInit> {
  const token = await getAuthToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
}

// Utility to make API calls with consistent error handling
export async function makeApiCall<T = any>({
  method,
  endpoint,
  data,
  config = {}
}: ApiCallOptions): Promise<T> {
  const headers = await createApiHeaders();
  
  const apiBaseUrl = process.env.API_BASE_URL || 'http://backend:8000';
  const url = `${apiBaseUrl}${endpoint}`;
  
  const requestOptions: RequestInit = {
    method,
    headers,
  };
  
  if (data && method !== 'GET') {
    requestOptions.body = JSON.stringify(data);
  }
  
  try {
    const response = await fetch(url, requestOptions);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    // Handle empty responses
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const jsonData = await response.json();
      return jsonData;
    }
    
    // For non-JSON responses (like DELETE operations), return a success indicator
    if (response.status >= 200 && response.status < 300) {
      return { success: true } as T;
    }
    
    // If we get here, something unexpected happened
    throw new Error(`Unexpected response: ${response.status} ${response.statusText}`);
  } catch (error) {
    throw new Error(`API call failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

// Utility to handle server action success
export function handleServerActionSuccess(config: ServerActionConfig = {}): void {
  const { revalidatePaths = [], redirectPath, successMessage } = config;
  
  // Revalidate paths for cache invalidation
  revalidatePaths.forEach(path => {
    revalidatePath(path);
  });
  
  // Show success notification if message provided
  if (successMessage) {
    // Note: In server actions, we can't directly call showSuccessNotification
    // This would need to be handled by the client component
    console.log(`Success: ${successMessage}`);
  }
  
  // Redirect if path provided
  if (redirectPath) {
    redirect(redirectPath);
  }
}

// Utility to handle server action errors
export function handleServerActionError(error: unknown, context: string = 'Server Action'): never {
  const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
  
  console.error(`[${context}] Error:`, {
    message: errorMessage,
    originalError: error,
    timestamp: new Date().toISOString()
  });
  
  throw new Error(`${context} failed: ${errorMessage}`);
}

// Utility to validate data with Zod schema
export function validateData<T>(schema: z.ZodSchema<T>, data: unknown): T {
  try {
    return schema.parse(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessage = error.errors.map(e => `${e.path.join('.')}: ${e.message}`).join(', ');
      throw new Error(`Validation failed: ${errorMessage}`);
    }
    throw error;
  }
}

// Utility to create a standardized server action wrapper
export function createServerAction<TInput, TOutput>(
  action: (input: TInput, config?: ServerActionConfig) => Promise<TOutput>,
  schema?: z.ZodSchema<TInput>
) {
  return async (input: TInput, config?: ServerActionConfig): Promise<TOutput> => {
    try {
      // Validate input if schema provided
      const validatedInput = schema ? validateData(schema, input) : input;
      
      // Execute the action
      const result = await action(validatedInput, config);
      
      // Handle success
      handleServerActionSuccess(config);
      
      return result;
    } catch (error) {
      // Handle error
      handleServerActionError(error, config?.errorContext || 'Server Action');
    }
  };
}

// Utility to create a simple GET server action
export function createGetServerAction<T = any>(
  endpoint: string,
  config?: ServerActionConfig
) {
  return async (): Promise<T> => {
    try {
      const result = await makeApiCall<T>({
        method: 'GET',
        endpoint,
        config
      });
      
      handleServerActionSuccess(config);
      return result;
    } catch (error) {
      handleServerActionError(error, config?.errorContext || 'GET Request');
    }
  };
}

// Utility to create a simple POST server action
export function createPostServerAction<TInput, TOutput = any>(
  endpoint: string,
  schema?: z.ZodSchema<TInput>,
  config?: ServerActionConfig
) {
  return async (data: TInput): Promise<TOutput> => {
    try {
      const validatedData = schema ? validateData(schema, data) : data;
      
      const result = await makeApiCall<TOutput>({
        method: 'POST',
        endpoint,
        data: validatedData,
        config
      });
      
      handleServerActionSuccess(config);
      return result;
    } catch (error) {
      handleServerActionError(error, config?.errorContext || 'POST Request');
    }
  };
}

// Utility to create a simple PUT server action
export function createPutServerAction<TInput, TOutput = any>(
  endpoint: string,
  schema?: z.ZodSchema<TInput>,
  config?: ServerActionConfig
) {
  return async (data: TInput): Promise<TOutput> => {
    try {
      const validatedData = schema ? validateData(schema, data) : data;
      
      const result = await makeApiCall<TOutput>({
        method: 'PUT',
        endpoint,
        data: validatedData,
        config
      });
      
      handleServerActionSuccess(config);
      return result;
    } catch (error) {
      handleServerActionError(error, config?.errorContext || 'PUT Request');
    }
  };
}

// Utility to create a simple DELETE server action
export function createDeleteServerAction<TOutput = any>(
  endpoint: string,
  config?: ServerActionConfig
) {
  return async (): Promise<TOutput> => {
    try {
      const result = await makeApiCall<TOutput>({
        method: 'DELETE',
        endpoint,
        config
      });
      
      handleServerActionSuccess(config);
      return result;
    } catch (error) {
      handleServerActionError(error, config?.errorContext || 'DELETE Request');
    }
  };
} 