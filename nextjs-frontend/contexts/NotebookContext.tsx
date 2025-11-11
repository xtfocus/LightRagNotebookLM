'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { NotebookPublic } from '@/app/openapi-client/types.gen';
import { fetchNotebooks, updateNotebook, deleteNotebook } from '@/components/actions/notebooks-action';
import { showErrorNotification, showSuccessNotification } from '@/lib/error-handling';
import { useNotifications } from '@/components/ui/NotificationContext';
import { validateNotebookArray, validateNotebookFormData } from '@/lib/type-validation';

interface NotebookContextType {
  // Notebook operations
  notebooks: NotebookPublic[];
  loading: boolean;
  error: string | null;
  editingNotebook: NotebookPublic | null;
  isEditModalOpen: boolean;
  loadNotebooks: () => Promise<void>;
  handleEdit: (notebook: NotebookPublic) => void;
  handleSaveEdit: (notebookId: string, title: string, description: string) => Promise<void>;
  handleDelete: (notebookId: string) => Promise<void>;
  closeEditModal: () => void;
  clearError: () => void;
  
  // Source count management
  sourceCount: number;
  setSourceCount: (count: number) => void;
  incrementSourceCount: () => void;
  decrementSourceCount: () => void;
  
  // Source selection management
  selectedSources: Set<string>;
  toggleSourceSelection: (sourceId: string) => void;
  selectAllSources: (sourceIds: string[]) => void;
  deselectAllSources: () => void;
  isSourceSelected: (sourceId: string) => boolean;
}

const NotebookContext = createContext<NotebookContextType | undefined>(undefined);

interface NotebookProviderProps {
  children: ReactNode;
  notebookId?: string;
  initialSourceCount?: number;
}

export function NotebookProvider({ children, notebookId, initialSourceCount = 0 }: NotebookProviderProps) {
  // Notebook operations state
  const [notebooks, setNotebooks] = useState<NotebookPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingNotebook, setEditingNotebook] = useState<NotebookPublic | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  
  // Source count state
  const [sourceCount, setSourceCount] = useState(initialSourceCount);
  
  // Source selection state with localStorage persistence (notebook-specific)
  const [selectedSources, setSelectedSources] = useState<Set<string>>(() => {
    // Initialize from localStorage if available (notebook-specific)
    if (typeof window !== 'undefined' && notebookId) {
      const storageKey = `notebook-selected-sources-${notebookId}`;
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        try {
          return new Set(JSON.parse(saved));
        } catch (error) {
          console.warn('Failed to parse saved source selections:', error);
        }
      }
    }
    return new Set();
  });
  
  const { addNotification } = useNotifications();

  // Clear selected sources when notebookId changes
  React.useEffect(() => {
    if (notebookId) {
      // Load notebook-specific selected sources
      const storageKey = `notebook-selected-sources-${notebookId}`;
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        try {
          const sources = new Set<string>(JSON.parse(saved));
          setSelectedSources(sources);
        } catch (error) {
          console.warn('Failed to parse saved source selections:', error);
          setSelectedSources(new Set());
        }
      } else {
        setSelectedSources(new Set());
      }
    }
  }, [notebookId]);

  const loadNotebooks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetchNotebooks();
      
      let validatedNotebooks: NotebookPublic[];
      
      if (Array.isArray(response)) {
        validatedNotebooks = validateNotebookArray(response);
      } else if (response && 'data' in response && Array.isArray(response.data)) {
        validatedNotebooks = validateNotebookArray(response.data);
      } else {
        validatedNotebooks = [];
      }
      
      setNotebooks(validatedNotebooks);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load notebooks';
      setError(errorMessage);
      showErrorNotification(addNotification, err, 'Loading Notebooks');
    } finally {
      setLoading(false);
    }
  }, [addNotification]);

  const handleEdit = useCallback((notebook: NotebookPublic) => {
    setEditingNotebook(notebook);
    setIsEditModalOpen(true);
  }, []);

  const handleSaveEdit = useCallback(async (notebookId: string, title: string, description: string) => {
    try {
      // Validate form data
      const formData = validateNotebookFormData({ title, description });
      
      await updateNotebook(notebookId, formData);
      
      // Update local state
      setNotebooks(prev => prev.map(notebook => 
        notebook.id === notebookId 
          ? { ...notebook, title: formData.title, description: formData.description }
          : notebook
      ));
      
      setEditingNotebook(null);
      setIsEditModalOpen(false);
      showSuccessNotification(addNotification, 'Notebook updated successfully');
    } catch (err) {
      showErrorNotification(addNotification, err, 'Updating Notebook');
    }
  }, [addNotification]);

  const handleDelete = useCallback(async (notebookId: string) => {
    try {
      await deleteNotebook(notebookId);
      
      // Update local state
      setNotebooks(prev => prev.filter(notebook => notebook.id !== notebookId));
      showSuccessNotification(addNotification, 'Notebook deleted successfully');
    } catch (err) {
      showErrorNotification(addNotification, err, 'Deleting Notebook');
    }
  }, [addNotification]);

  const closeEditModal = useCallback(() => {
    setIsEditModalOpen(false);
    setEditingNotebook(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Source count functions
  const incrementSourceCount = () => {
    setSourceCount(prev => prev + 1);
  };

  const decrementSourceCount = () => {
    setSourceCount(prev => Math.max(0, prev - 1));
  };

  // Source selection functions
  const toggleSourceSelection = useCallback((sourceId: string) => {
    setSelectedSources(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sourceId)) {
        newSet.delete(sourceId);
      } else {
        newSet.add(sourceId);
      }
      
      // Save to localStorage (notebook-specific)
      if (typeof window !== 'undefined' && notebookId) {
        const storageKey = `notebook-selected-sources-${notebookId}`;
        localStorage.setItem(storageKey, JSON.stringify(Array.from(newSet)));
      }
      
      return newSet;
    });
  }, [notebookId]);

  const selectAllSources = useCallback((sourceIds: string[]) => {
    const newSet = new Set(sourceIds);
    setSelectedSources(newSet);
    // Save to localStorage (notebook-specific)
    if (typeof window !== 'undefined' && notebookId) {
      const storageKey = `notebook-selected-sources-${notebookId}`;
      localStorage.setItem(storageKey, JSON.stringify(Array.from(newSet)));
    }
  }, [notebookId]);

  const deselectAllSources = useCallback(() => {
    setSelectedSources(new Set());
    // Clear localStorage (notebook-specific)
    if (typeof window !== 'undefined' && notebookId) {
      const storageKey = `notebook-selected-sources-${notebookId}`;
      localStorage.removeItem(storageKey);
    }
  }, [notebookId]);

  const isSourceSelected = useCallback((sourceId: string) => {
    return selectedSources.has(sourceId);
  }, [selectedSources]);

  return (
    <NotebookContext.Provider
      value={{
        // Notebook operations
    notebooks,
    loading,
    error,
    editingNotebook,
    isEditModalOpen,
    loadNotebooks,
    handleEdit,
    handleSaveEdit,
    handleDelete,
    closeEditModal,
    clearError,
        
        // Source count management
        sourceCount,
        setSourceCount,
        incrementSourceCount,
        decrementSourceCount,
        
        // Source selection management
        selectedSources,
        toggleSourceSelection,
        selectAllSources,
        deselectAllSources,
        isSourceSelected,
      }}
    >
      {children}
    </NotebookContext.Provider>
  );
}

export function useNotebooks() {
  const context = useContext(NotebookContext);
  if (context === undefined) {
    throw new Error('useNotebooks must be used within a NotebookProvider');
  }
  return context;
}

export function useNotebook() {
  const context = useContext(NotebookContext);
  if (context === undefined) {
    throw new Error('useNotebook must be used within a NotebookProvider');
  }
  return context;
} 