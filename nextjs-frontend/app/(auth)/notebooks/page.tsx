"use client";

import { CreateNotebookTile } from '@/components/notebooks/CreateNotebookTile';
import { NotebookCard } from '@/components/notebooks/NotebookCard';
import { EditNotebookModal } from '@/components/notebooks/EditNotebookModal';
import { useNotebooks } from '@/contexts/NotebookContext';
import { NotebookProvider } from '@/contexts/NotebookContext';
import { useNotebookList } from '@/hooks/useNotebookList';
import { 
  NotebookListLoading, 
  NotebookListError, 
  NotebookListHeader 
} from '@/components/notebooks/NotebookListStates';

function NotebooksPageContent() {
  const {
    notebooks,
    loading,
    error,
    loadNotebooks,
    clearError,
  } = useNotebookList();

  const {
    editingNotebook,
    isEditModalOpen,
  } = useNotebooks();

  const handleRetry = () => {
    clearError();
    loadNotebooks();
  };

  if (loading) {
    return (
      <NotebookListLoading
        title="Notebooks"
        description="Create and manage your AI-powered notebooks with document context"
      />
    );
  }

  if (error) {
    return (
      <NotebookListError
        title="Notebooks"
        description="Create and manage your AI-powered notebooks with document context"
        error={error}
        onRetry={handleRetry}
      />
    );
  }

  return (
    <div className="container mx-auto p-6">
      <NotebookListHeader
        title="Notebooks"
        description="Create and manage your AI-powered notebooks with document context"
      />
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <CreateNotebookTile onNotebookCreated={loadNotebooks} />
        {notebooks.map((notebook) => (
          <NotebookCard 
            key={notebook.id} 
            notebook={notebook} 
          />
        ))}
      </div>
      <EditNotebookModal 
        notebook={editingNotebook} 
        isOpen={isEditModalOpen} 
      />
    </div>
  );
}

export default function NotebooksPage() {
  return (
    <NotebookProvider>
      <NotebooksPageContent />
    </NotebookProvider>
  );
} 