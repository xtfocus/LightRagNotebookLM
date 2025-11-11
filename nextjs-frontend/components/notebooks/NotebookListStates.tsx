import { 
  NotebookListLoadingProps, 
  NotebookListErrorProps, 
  NotebookListHeaderProps 
} from '@/types/notebook';

export function NotebookListLoading({ title, description }: NotebookListLoadingProps) {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
        <p className="text-gray-600 mt-2">{description}</p>
      </div>
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading notebooks...</div>
      </div>
    </div>
  );
}

export function NotebookListError({ title, description, error, onRetry }: NotebookListErrorProps) {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
        <p className="text-gray-600 mt-2">{description}</p>
      </div>
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-lg text-red-600 mb-4">Error: {error}</div>
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    </div>
  );
}

export function NotebookListHeader({ title, description }: NotebookListHeaderProps) {
  return (
    <div className="mb-8">
      <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
      <p className="text-gray-600 mt-2">{description}</p>
    </div>
  );
} 