import { fetchNotebook } from "@/components/actions/notebooks-action";
import { fetchNotebookSources } from "@/components/actions/sources-action";
import { SourcesSidebar } from "@/components/notebooks/SourcesSidebar";
import { ChatArea } from "@/components/notebooks/ChatArea";
import { NotebookProvider } from "@/contexts/NotebookContext";
import { notFound } from "next/navigation";

interface NotebookWorkspacePageProps {
  params: Promise<{ id: string }>;
}

// UUID validation function
function isValidUUID(uuid: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
}

export default async function NotebookWorkspacePage({ params }: NotebookWorkspacePageProps) {
  const { id: notebookId } = await params;
  
  // Debug logging
  console.log('NotebookWorkspacePage - Received notebookId:', notebookId);
  console.log('NotebookWorkspacePage - notebookId type:', typeof notebookId);
  console.log('NotebookWorkspacePage - notebookId length:', notebookId?.length);
  
  // Additional validation for common problematic patterns
  if (notebookId?.includes('.js.map') || notebookId?.includes('.map')) {
    console.error('Source map file detected in notebookId:', notebookId);
    notFound();
  }
  
  // Validate notebook ID
  if (!isValidUUID(notebookId)) {
    console.error('Invalid notebook ID format:', notebookId);
    // Use Next.js notFound() for invalid UUIDs instead of showing error page
    notFound();
  }
  
  try {
  // Fetch notebook data
  const notebookResponse = await fetchNotebook(notebookId);
  
  // Handle error response
  if ('message' in notebookResponse) {
      console.error('Failed to fetch notebook:', notebookResponse.message);
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-red-600">Error: {String(notebookResponse.message)}</div>
      </div>
    );
  }

  const notebook = notebookResponse;

  // Fetch initial source count for this notebook
  let initialSourceCount = 0;
  try {
    const sourcesResponse = await fetchNotebookSources(notebookId);
    if (sourcesResponse && 'data' in sourcesResponse) {
      initialSourceCount = sourcesResponse.data.length;
    }
  } catch (error) {
    console.warn('Failed to fetch initial source count:', error);
    // Continue with 0 as fallback
  }

  return (
    <NotebookProvider notebookId={notebookId} initialSourceCount={initialSourceCount}>
    <div className="overflow-hidden flex flex-col" style={{ height: 'calc(100vh - 120px)' }}>
      {/* Minimal Title Bar */}
      <div className="flex items-center px-5 py-3 flex-shrink-0">
        <h1 
          className="font-bold text-gray-900" 
          style={{ fontSize: '18px' }}
        >
          {notebook.title}
        </h1>
      </div>
      
      {/* Main Workspace - Panels */}
      <div className="flex gap-5 flex-1 px-5 pb-5 overflow-hidden min-h-0">
        {/* Sources Panel */}
          <SourcesSidebar notebookId={notebookId} />
        
        {/* Chat Panel */}
          <ChatArea notebookId={notebookId} />
      </div>
    </div>
    </NotebookProvider>
  );
  } catch (error) {
    console.error('Unexpected error in NotebookWorkspacePage:', error);
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-red-600">
          An unexpected error occurred. Please try again.
        </div>
      </div>
    );
  }
} 