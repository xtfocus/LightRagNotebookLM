'use client';

import { useState, useEffect } from 'react';
import { Menu, Plus, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { spacing, borderRadius } from '@/lib/design-system';
import { AddSourcesModal } from './AddSourcesModal';
import { SourceList } from './SourceList';
import { useNotebook } from '@/contexts/NotebookContext';
import { fetchNotebookSources } from '@/components/actions/sources-action';

interface SourcesSidebarProps {
  notebookId: string;
}

export function SourcesSidebar({ notebookId }: SourcesSidebarProps) {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const { sourceCount, setSourceCount, incrementSourceCount, decrementSourceCount } = useNotebook();
  const maxSources = 5; // This could come from a config or API

  // Sync source count with backend data when component loads
  useEffect(() => {
    const syncSourceCount = async () => {
      try {
        const sourcesResponse = await fetchNotebookSources(notebookId);
        if (sourcesResponse && 'data' in sourcesResponse) {
          const actualCount = sourcesResponse.data.length;
          setSourceCount(actualCount);
        }
      } catch (error) {
        console.warn('Failed to sync source count:', error);
      }
    };

    syncSourceCount();
  }, [notebookId, setSourceCount]);

  const handleSourceAdded = () => {
    incrementSourceCount();
    // Trigger a refresh of the SourceList
    setRefreshKey(prev => prev + 1);
  };

  const handleSourceRemoved = () => {
    decrementSourceCount();
    // Trigger a refresh of the SourceList
    setRefreshKey(prev => prev + 1);
  };

  return (
    <>
    <section 
      className="source-panel bg-white rounded-lg shadow-sm flex flex-col overflow-hidden min-h-0"
      style={{ 
        width: '25vw',
        minWidth: '320px',
        maxHeight: '100%'
      }}
    >
      {/* Panel Header */}
      <div className="panel-header flex items-center justify-between p-4 border-b border-gray-100 flex-shrink-0">
        <h2 className="text-sm font-medium text-gray-900" style={{ fontSize: '14px' }}>
          Sources
        </h2>
        <button className="p-1 hover:bg-gray-200 rounded transition-colors">
          <Menu className="h-4 w-4 text-gray-500" />
        </button>
      </div>

      {/* Source Picker Content */}
      <div className="source-panel-content flex-1 flex flex-col overflow-hidden min-h-0">
        {/* Button Row */}
        <div className="button-row flex gap-2 p-4 border-b border-gray-100 flex-shrink-0">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 justify-start"
              onClick={() => setIsAddModalOpen(true)}
              disabled={sourceCount >= maxSources}
            style={{
              backgroundColor: '#f3f4f6',
              borderColor: '#d1d5db',
              color: '#374151',
              padding: `${spacing.sm} ${spacing.md}`,
              borderRadius: borderRadius.md,
            }}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="flex-1 justify-start"
            style={{
              backgroundColor: '#f3f4f6',
              borderColor: '#d1d5db',
              color: '#374151',
              padding: `${spacing.sm} ${spacing.md}`,
              borderRadius: borderRadius.md,
            }}
          >
            <Search className="h-4 w-4 mr-2" />
            Discover
          </Button>
        </div>

        {/* Scrollable Content Area */}
          <div className="scroll-container flex-1 overflow-y-auto min-h-0">
            <div className="scroll-area p-4">
              <SourceList 
                notebookId={notebookId}
                onSourceRemoved={handleSourceRemoved}
                refreshKey={refreshKey}
              />
          </div>
        </div>
      </div>
    </section>

      {/* Add Sources Modal */}
      <AddSourcesModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        notebookId={notebookId}
        currentSourceCount={sourceCount}
        maxSources={maxSources}
        onSourceAdded={handleSourceAdded}
      />
    </>
  );
} 