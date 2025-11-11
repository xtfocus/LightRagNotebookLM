import { useState, useCallback } from 'react';
import { useNotebooks } from '@/contexts/NotebookContext';

interface UseNotebookOperationsReturn {
  // Delete operations
  isDeleting: boolean;
  showDeleteConfirm: boolean;
  handleDeleteClick: () => void;
  handleConfirmDelete: (notebookId: string) => Promise<void>;
  handleCancelDelete: () => void;
  
  // Edit operations
  handleEditClick: (notebookId: string) => void;
}

export function useNotebookOperations(): UseNotebookOperationsReturn {
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const { handleDelete } = useNotebooks();

  const handleDeleteClick = useCallback(() => {
    setShowDeleteConfirm(true);
  }, []);

  const handleConfirmDelete = useCallback(async (notebookId: string) => {
    setIsDeleting(true);
    try {
      await handleDelete(notebookId);
      setShowDeleteConfirm(false);
    } finally {
      setIsDeleting(false);
    }
  }, [handleDelete]);

  const handleCancelDelete = useCallback(() => {
    setShowDeleteConfirm(false);
  }, []);

  const handleEditClick = useCallback((notebookId: string) => {
    // This will be implemented when we have the notebook data
    // For now, we'll need to pass the full notebook object
  }, []);

  return {
    isDeleting,
    showDeleteConfirm,
    handleDeleteClick,
    handleConfirmDelete,
    handleCancelDelete,
    handleEditClick,
  };
} 