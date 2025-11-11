'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { 
  makeApiCall,
  ServerActionConfig 
} from '@/lib/server-actions';
import { notebookSchema } from '@/lib/definitions';

// Type definitions
export interface NotebookCreate {
  title: string;
  description?: string;
}

export interface NotebookUpdate {
  title?: string;
  description?: string;
}

// Server actions using utility functions
export async function fetchNotebooks() {
  try {
    const result = await makeApiCall<{ data: any[] }>({
      method: 'GET',
      endpoint: '/api/v1/notebooks/',
    });
    
    return result;
  } catch (error) {
    console.error('[Notebook List] Error:', error);
    throw error;
  }
}

export async function fetchNotebook(id: string) {
  try {
    const result = await makeApiCall<any>({
      method: 'GET',
      endpoint: `/api/v1/notebooks/${id}/`,
    });
    
    return result;
  } catch (error) {
    console.error('[Notebook Details] Error:', error);
    throw error;
  }
}

export async function createNotebook(data: NotebookCreate) {
  try {
    // Validate the data
    const validatedData = notebookSchema.parse(data);
    
    const result = await makeApiCall<any>({
      method: 'POST',
      endpoint: '/api/v1/notebooks/',
      data: validatedData,
    });
    
    // Revalidate and redirect on success
    revalidatePath('/notebooks');
    redirect('/notebooks');
    
    return result;
  } catch (error) {
    console.error('[Notebook Creation] Error:', error);
    throw error;
  }
}

export async function updateNotebook(id: string, data: NotebookUpdate) {
  try {
    // Validate the data
    const updateSchema = z.object({
      title: z.string().optional(),
      description: z.string().optional()
    });
    const validatedData = updateSchema.parse(data);
    
    const result = await makeApiCall<any>({
      method: 'PUT',
      endpoint: `/api/v1/notebooks/${id}/`,
      data: validatedData,
    });
    
    // Revalidate on success
    revalidatePath('/notebooks');
    
    return result;
  } catch (error) {
    console.error('[Notebook Update] Error:', error);
    throw error;
  }
}

export async function deleteNotebook(id: string) {
  try {
    const result = await makeApiCall<any>({
      method: 'DELETE',
      endpoint: `/api/v1/notebooks/${id}/`,
    });
    
    // Revalidate on success
    revalidatePath('/notebooks');
    
    return result;
  } catch (error) {
    console.error('[Notebook Deletion] Error:', error);
    throw error;
  }
} 