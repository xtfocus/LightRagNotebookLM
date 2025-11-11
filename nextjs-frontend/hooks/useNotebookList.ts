import { useEffect } from 'react';
import { useNotebooks } from '@/contexts/NotebookContext';
import { UseNotebookListReturn } from '@/types/notebook';

export function useNotebookList(): UseNotebookListReturn {
  const {
    notebooks,
    loading,
    error,
    loadNotebooks,
    clearError,
  } = useNotebooks();

  useEffect(() => {
    loadNotebooks();
  }, [loadNotebooks]);

  return {
    notebooks,
    loading,
    error,
    loadNotebooks,
    clearError,
  };
} 