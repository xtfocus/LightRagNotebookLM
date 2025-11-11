"use client";

import { NotebookPublic } from "@/app/openapi-client/types.gen";
import { useNotebooks } from "@/contexts/NotebookContext";
import { ConfirmationModal } from '@/components/ui/ConfirmationModal';
import { useDateFormatting } from '@/hooks/useDateFormatting';
import { useNotebookOperations } from '@/hooks/useNotebookOperations';
import { NotebookCardUI } from './NotebookCardUI';

// Extended interface to include source_count (will be available after backend update)
interface NotebookWithSourceCount extends NotebookPublic {
  source_count?: number;
}

interface NotebookCardProps {
  notebook: NotebookWithSourceCount;
}

export function NotebookCard({ notebook }: NotebookCardProps) {
  const { handleEdit } = useNotebooks();
  const { formatDate } = useDateFormatting();
  const {
    isDeleting,
    showDeleteConfirm,
    handleDeleteClick,
    handleConfirmDelete,
    handleCancelDelete,
  } = useNotebookOperations();

  const handleConfirmDeleteWithId = async () => {
    await handleConfirmDelete(notebook.id);
  };

  const handleEditClick = () => {
    handleEdit(notebook);
  };

  return (
    <>
      <NotebookCardUI
        id={notebook.id}
        title={notebook.title}
        description={notebook.description || undefined}
        updatedAt={notebook.updated_at}
        sourceCount={notebook.source_count || 0} // Use actual source count from backend
        onEdit={handleEditClick}
        onDelete={() => {}} // Not used in UI component
        onDeleteClick={handleDeleteClick}
        isDeleting={isDeleting}
        formattedDate={formatDate(notebook.updated_at)}
      />

      <ConfirmationModal
        isOpen={showDeleteConfirm}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDeleteWithId}
        title="Delete Notebook"
        message={`Are you sure you want to delete "${notebook.title}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={isDeleting}
      />
    </>
  );
} 