'use client';

import React, { useState, useEffect } from 'react';
import { FileText, Globe, Trash2, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { colors } from '@/lib/design-system';
import { useNotebook } from '@/contexts/NotebookContext';
import { getMappedStatusIcon, getMappedStatusText, getSourceStatus } from '@/lib/source-utils';

interface Source {
  id: string;
  source: {
    id: string;
    title: string;
    source_type: 'document' | 'url' | 'video' | 'image' | 'text';
    source_metadata: Record<string, any>;
    status: 'pending' | 'processing' | 'indexed' | 'failed';
    created_at: string;
  };
  added_at: string;
  position: number;
}

interface SourceListProps {
  notebookId: string;
  onSourceRemoved: () => void;
  refreshKey?: number;
}

const getSourceIcon = (sourceType: string) => {
  switch (sourceType) {
    case 'document':
      return <FileText className="h-4 w-4" />;
    case 'url':
      return <Globe className="h-4 w-4" />;
    case 'video':
      return <FileText className="h-4 w-4" />; // TODO: Add video icon
    case 'image':
      return <FileText className="h-4 w-4" />; // TODO: Add image icon
    case 'text':
      return <FileText className="h-4 w-4" />; // TODO: Add text icon
    default:
      return <FileText className="h-4 w-4" />;
  }
};



export function SourceList({ notebookId, onSourceRemoved, refreshKey }: SourceListProps) {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [removingSource, setRemovingSource] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  
  // Get source selection functions from context
  const { toggleSourceSelection, isSourceSelected, selectAllSources, deselectAllSources } = useNotebook();

  const fetchSources = async () => {
    try {
      console.log('SourceList: fetchSources called for notebookId:', notebookId);
      setLoading(true);
      setError(null);
      
      const { fetchNotebookSources } = await import('@/components/actions/sources-action');
      console.log('SourceList: fetchNotebookSources imported');
      const result = await fetchNotebookSources(notebookId);
      console.log('SourceList: fetchNotebookSources result:', result);
      
      if ('data' in result) {
        console.log('SourceList: Setting sources:', result.data);
        setSources(result.data);
      } else {
        console.error('SourceList: Invalid result structure:', result);
        setError('Failed to fetch sources');
      }
    } catch (err) {
      console.error('SourceList: Error fetching sources:', err);
      setError('Failed to load sources');
    } finally {
      setLoading(false);
    }
  };

  const removeSource = async (sourceId: string) => {
    try {
      setRemovingSource(sourceId);
      
      const { removeSourceFromNotebook } = await import('@/components/actions/sources-action');
      await removeSourceFromNotebook(notebookId, sourceId);
      
      // Remove from local state
      setSources(prev => prev.filter(s => s.source.id !== sourceId));
      onSourceRemoved();
    } catch (err) {
      console.error('Error removing source:', err);
      // You might want to show a toast notification here
    } finally {
      setRemovingSource(null);
    }
  };

  // Check if any sources are still processing
  const hasProcessingSources = sources.some(source => 
    source.source.status === 'pending' || source.source.status === 'processing'
  );

  // Start/stop polling based on processing status
  useEffect(() => {
    if (hasProcessingSources) {
      // Start polling every 3 seconds for sources that are processing
      const interval = setInterval(() => {
        fetchSources();
      }, 3000);
      setPollingInterval(interval);
    } else {
      // Stop polling if no sources are processing
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    }

    // Cleanup on unmount
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [hasProcessingSources]);

  useEffect(() => {
    fetchSources();
  }, [notebookId, refreshKey]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 text-gray-400 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <AlertCircle className="h-6 w-6 text-red-500 mx-auto mb-2" />
          <p className="text-sm text-red-600">{error}</p>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchSources}
            className="mt-2"
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (sources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <FileText 
          className="h-12 w-12 mb-4" 
          style={{ color: colors.gray[400] }}
        />
        <span className="font-medium text-gray-600 mb-2" style={{ fontSize: '14px' }}>
          Saved sources will appear here
        </span>
        <span className="text-gray-500 leading-relaxed" style={{ fontSize: '13px' }}>
          Click Add source above to add PDFs, websites, text, videos or audio files. Or import a file directly from Google Drive.
        </span>
      </div>
    );
  }

  // Calculate selection summary
  const selectedCount = sources.filter(source => isSourceSelected(source.source.id)).length;
  const totalCount = sources.length;

  return (
    <div className="space-y-3">
      {/* Selection Summary */}
      {totalCount > 0 && (
        <div className="flex items-center justify-between text-sm text-gray-600 px-1">
          <span>
            {selectedCount} of {totalCount} source{totalCount !== 1 ? 's' : ''} selected
          </span>
          {selectedCount > 0 && (
            <button
              onClick={() => {
                if (selectedCount === totalCount) {
                  deselectAllSources();
                } else {
                  selectAllSources(sources.map(source => source.source.id));
                }
              }}
              className="text-blue-600 hover:text-blue-800 text-xs underline"
            >
              {selectedCount === totalCount ? 'Deselect all' : 'Select all'}
            </button>
          )}
        </div>
      )}
      
      <div className="space-y-2">
        {sources.map((source) => {
        const status = getSourceStatus(source);
        const isRemoving = removingSource === source.source.id;
        
        return (
          <div
            key={source.source.id}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center space-x-3 min-w-0 flex-1">
              {/* Checkbox for source selection */}
              <div className="flex-shrink-0">
                <input
                  type="checkbox"
                  checked={isSourceSelected(source.source.id)}
                  onChange={() => toggleSourceSelection(source.source.id)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded cursor-pointer"
                />
              </div>
              
              <div className="flex-shrink-0">
                {getSourceIcon(source.source.source_type)}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {source.source.title}
                </p>
                <div className="flex items-center space-x-2 mt-1">
                    {getMappedStatusIcon(status)}
                  <span className="text-xs text-gray-500">
                      {getMappedStatusText(status)}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex-shrink-0">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeSource(source.source.id)}
                disabled={isRemoving}
                className="h-6 w-6 p-0 text-gray-400 hover:text-red-500"
              >
                {isRemoving ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Trash2 className="h-3 w-3" />
                )}
              </Button>
            </div>
          </div>
        );
      })}
      </div>
    </div>
  );
} 