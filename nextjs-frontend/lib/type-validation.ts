import { NotebookPublic } from '@/app/openapi-client/types.gen';

// Type guards for runtime validation
export function isNotebookPublic(obj: unknown): obj is NotebookPublic {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'title' in obj &&
    'description' in obj &&
    'created_at' in obj &&
    'updated_at' in obj &&
    'owner_id' in obj &&
    typeof (obj as any).id === 'string' &&
    typeof (obj as any).title === 'string' &&
    (typeof (obj as any).description === 'string' || (obj as any).description === null) &&
    typeof (obj as any).created_at === 'string' &&
    typeof (obj as any).updated_at === 'string' &&
    typeof (obj as any).owner_id === 'string'
  );
}

export function isNotebookPublicArray(arr: unknown): arr is NotebookPublic[] {
  return Array.isArray(arr) && arr.every(isNotebookPublic);
}

// Validation functions
export function validateNotebookData(data: unknown): NotebookPublic {
  if (!isNotebookPublic(data)) {
    throw new Error('Invalid notebook data structure');
  }
  return data;
}

export function validateNotebookArray(data: unknown): NotebookPublic[] {
  if (!isNotebookPublicArray(data)) {
    throw new Error('Invalid notebook array structure');
  }
  return data;
}

// Form validation
export function validateNotebookFormData(data: unknown): { title: string; description?: string } {
  if (
    typeof data === 'object' &&
    data !== null &&
    'title' in data &&
    typeof (data as any).title === 'string'
  ) {
    const result: { title: string; description?: string } = {
      title: (data as any).title,
    };
    
    if ('description' in data && typeof (data as any).description === 'string') {
      result.description = (data as any).description;
    }
    
    return result;
  }
  
  throw new Error('Invalid notebook form data structure');
}

// API response validation
export function validateApiResponse<T>(response: unknown, validator: (data: unknown) => T): T {
  if (
    typeof response === 'object' &&
    response !== null &&
    'data' in response
  ) {
    return validator((response as any).data);
  }
  
  throw new Error('Invalid API response structure');
}

// Error validation
export function validateError(error: unknown): { message: string; status?: number } {
  if (error instanceof Error) {
    return { message: error.message };
  }
  
  if (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as any).message === 'string'
  ) {
    const result: { message: string; status?: number } = {
      message: (error as any).message,
    };
    
    if ('status' in error && typeof (error as any).status === 'number') {
      result.status = (error as any).status;
    }
    
    return result;
  }
  
  return { message: 'Unknown error occurred' };
} 