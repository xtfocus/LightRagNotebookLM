'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { 
  makeApiCall,
  ServerActionConfig,
  getAuthToken
} from '@/lib/server-actions';
import { sourceCreateSchema, urlInputSchema, notebookSourceCreateSchema } from '@/lib/definitions';

// Type definitions
export interface SourceCreate {
  title: string;
  description?: string;
  source_type: 'document' | 'url' | 'video' | 'image' | 'text';
  source_metadata?: Record<string, any>;
}

export interface SourceUpdate {
  title?: string;
  description?: string;
  source_metadata?: Record<string, any>;
}

export interface UrlInput {
  url: string;
  title?: string;
  description?: string;
}

export interface NotebookSourceCreate {
  source_id: string;
  position?: number;
}

// Source CRUD operations
export async function fetchSources(sourceType?: string) {
  try {
    const params = sourceType ? `?source_type=${sourceType}` : '';
    const result = await makeApiCall<{ data: any[]; count: number }>({
      method: 'GET',
      endpoint: `/api/v1/sources/${params}`,
    });
    
    return result;
  } catch (error) {
    console.error('[Source List] Error:', error);
    throw error;
  }
}

export async function fetchSource(id: string) {
  try {
    const result = await makeApiCall<any>({
      method: 'GET',
      endpoint: `/api/v1/sources/${id}/`,
    });
    
    return result;
  } catch (error) {
    console.error('[Source Details] Error:', error);
    throw error;
  }
}

export async function createSource(data: SourceCreate) {
  try {
    // Validate the data
    const validatedData = sourceCreateSchema.parse(data);
    
    const result = await makeApiCall<any>({
      method: 'POST',
      endpoint: '/api/v1/sources/',
      data: validatedData,
    });
    
    // Revalidate on success
    revalidatePath('/notebooks');
    
    return result;
  } catch (error) {
    console.error('[Source Creation] Error:', error);
    throw error;
  }
}

export async function updateSource(id: string, data: SourceUpdate) {
  try {
    const result = await makeApiCall<any>({
      method: 'PUT',
      endpoint: `/api/v1/sources/${id}/`,
      data,
    });
    
    // Revalidate on success
    revalidatePath('/notebooks');
    
    return result;
  } catch (error) {
    console.error('[Source Update] Error:', error);
    throw error;
  }
}

export async function deleteSource(id: string) {
  try {
    const result = await makeApiCall<any>({
      method: 'DELETE',
      endpoint: `/api/v1/sources/${id}/`,
    });
    
    // Revalidate on success
    revalidatePath('/notebooks');
    
    return result;
  } catch (error) {
    console.error('[Source Deletion] Error:', error);
    throw error;
  }
}

// Notebook source management
export async function fetchNotebookSources(notebookId: string) {
  try {
    const result = await makeApiCall<{ data: any[]; count: number }>({
      method: 'GET',
      endpoint: `/api/v1/notebooks/${notebookId}/sources`,
    });
    
    return result;
  } catch (error) {
    console.error('[Notebook Sources List] Error:', error);
    throw error;
  }
}

export async function addSourceToNotebook(notebookId: string, data: NotebookSourceCreate) {
  try {
    // Validate the data
    const validatedData = notebookSourceCreateSchema.parse(data);
    
    const result = await makeApiCall<any>({
      method: 'POST',
      endpoint: `/api/v1/notebooks/${notebookId}/sources`,
      data: validatedData,
    });
    
    // Revalidate on success
    revalidatePath(`/notebooks/${notebookId}`);
    
    return result;
  } catch (error) {
    console.error('[Add Source to Notebook] Error:', error);
    throw error;
  }
}

export async function removeSourceFromNotebook(notebookId: string, sourceId: string) {
  try {
    const result = await makeApiCall<any>({
      method: 'DELETE',
      endpoint: `/api/v1/notebooks/${notebookId}/sources/${sourceId}`,
    });
    
    // Revalidate on success
    revalidatePath(`/notebooks/${notebookId}`);
    
    return result;
  } catch (error) {
    console.error('[Remove Source from Notebook] Error:', error);
    throw error;
  }
}

// File upload operations
export async function uploadFiles(files: File[]) {
  try {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    
    // For file uploads, we need to use fetch directly since makeApiCall doesn't support FormData
    const token = await getAuthToken();
    const apiBaseUrl = process.env.API_BASE_URL || 'http://backend:8000';
    const url = `${apiBaseUrl}/api/v1/uploads/files/`;
    
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    // Don't set Content-Type for FormData - browser will set it with boundary
    
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('[File Upload] Error:', error);
    throw error;
  }
}

// URL processing
export async function processUrl(data: UrlInput) {
  try {
    // Validate the data
    const validatedData = urlInputSchema.parse(data);
    
    // First create a URL source
    const sourceData: SourceCreate = {
      title: validatedData.title || validatedData.url,
      description: validatedData.description,
      source_type: 'url',
      source_metadata: {
        url: validatedData.url,
      },
    };
    
    const result = await createSource(sourceData);
    return result;
  } catch (error) {
    console.error('[URL Processing] Error:', error);
    throw error;
  }
} 