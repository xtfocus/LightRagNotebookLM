import { NotebookPublic } from '@/app/openapi-client/types.gen';

// Notebook operation types
export interface NotebookOperationState {
  isDeleting: boolean;
  showDeleteConfirm: boolean;
}

export interface NotebookOperationHandlers {
  handleDeleteClick: () => void;
  handleConfirmDelete: (notebookId: string) => Promise<void>;
  handleCancelDelete: () => void;
  handleEditClick: (notebookId: string) => void;
}

// Date formatting types
export interface DateFormattingOptions {
  year?: 'numeric' | '2-digit';
  month?: 'long' | 'short' | 'narrow' | 'numeric' | '2-digit';
  day?: 'numeric' | '2-digit';
  hour?: 'numeric' | '2-digit';
  minute?: 'numeric' | '2-digit';
  second?: 'numeric' | '2-digit';
}

export interface DateFormattingFunctions {
  formatDate: (dateString: string, options?: DateFormattingOptions) => string;
  formatDateTime: (dateString: string, options?: DateFormattingOptions) => string;
  formatRelativeTime: (dateString: string) => string;
}

// Modal state types
export interface ModalState {
  isOpen: boolean;
  openModal: () => void;
  closeModal: () => void;
  toggleModal: () => void;
}

// Notebook list types
export interface NotebookListState {
  notebooks: NotebookPublic[];
  loading: boolean;
  error: string | null;
}

export interface NotebookListHandlers {
  loadNotebooks: () => Promise<void>;
  clearError: () => void;
}

// UI Component prop types
export interface NotebookCardUIProps {
  // Data
  id: string;
  title: string;
  description?: string;
  updatedAt: string;
  sourceCount: number;
  
  // Actions
  onEdit: () => void;
  onDelete: () => void;
  onDeleteClick: () => void;
  
  // State
  isDeleting: boolean;
  
  // Formatting
  formattedDate: string;
}

export interface NotebookListLoadingProps {
  title: string;
  description: string;
}

export interface NotebookListErrorProps {
  title: string;
  description: string;
  error: string;
  onRetry: () => void;
}

export interface NotebookListHeaderProps {
  title: string;
  description: string;
}

// Hook return types
export interface UseNotebookOperationsReturn extends NotebookOperationState, NotebookOperationHandlers {}

export interface UseDateFormattingReturn extends DateFormattingFunctions {}

export interface UseModalStateReturn extends ModalState {}

export interface UseNotebookListReturn extends NotebookListState, NotebookListHandlers {}

// Form types
export interface NotebookFormData {
  title: string;
  description?: string;
}

export interface NotebookFormValidation {
  isValid: boolean;
  errors: Record<string, string>;
}

// API response types
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface ApiError {
  message: string;
  status: number;
  details?: string;
}

// Context types
export interface NotebookContextType {
  // State
  notebooks: NotebookPublic[];
  loading: boolean;
  error: string | null;
  editingNotebook: NotebookPublic | null;
  isEditModalOpen: boolean;

  // Actions
  loadNotebooks: () => Promise<void>;
  handleEdit: (notebook: NotebookPublic) => void;
  handleSaveEdit: (notebookId: string, title: string, description: string) => Promise<void>;
  handleDelete: (notebookId: string) => Promise<void>;
  closeEditModal: () => void;
  clearError: () => void;
} 