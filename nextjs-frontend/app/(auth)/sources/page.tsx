'use client';

import React, { useState, useEffect } from 'react';
import { Briefcase, Trash2, Globe, FileText, Loader2, AlertCircle, Plus, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ConfirmationModal } from '@/components/ui/ConfirmationModal';
import { showErrorNotification, showSuccessNotification } from '@/lib/error-handling';
import { useNotifications } from '@/components/ui/NotificationContext';
import { deleteSource, fetchSources } from '@/components/actions/sources-action';
import { getStatusIcon, getStatusText, getStatusBadgeVariant } from '@/lib/source-utils';
import { CreateSourceModal } from '@/components/sources/CreateSourceModal';

interface Source {
  id: string;
  title: string;
  source_type: 'document' | 'url' | 'video' | 'image' | 'text';
  source_metadata: Record<string, any>;
  status: 'pending' | 'processing' | 'indexed' | 'failed';
  created_at: string;
  notebook_count?: number;
}

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingSource, setDeletingSource] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [sourceToDelete, setSourceToDelete] = useState<Source | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const { addNotification } = useNotifications();

  const loadSources = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setIsRefreshing(true);
      } else {
      setLoading(true);
      }
      setError(null);
      
      const result = await fetchSources();
      if ('data' in result) {
        setSources(result.data);
      } else {
        setSources(result || []);
      }
    } catch (err) {
      console.error('Error fetching sources:', err);
      setError('Failed to load sources');
      showErrorNotification(addNotification, err, 'Loading Sources');
    } finally {
      if (isRefresh) {
        setIsRefreshing(false);
      } else {
      setLoading(false);
      }
    }
  };

  const handleDeleteClick = (source: Source) => {
    setSourceToDelete(source);
    setShowDeleteModal(true);
  };

  const handleConfirmDelete = async () => {
    if (!sourceToDelete) return;
    
    try {
      setDeletingSource(sourceToDelete.id);
      await deleteSource(sourceToDelete.id);
      
      // Remove from local state
      setSources(prev => prev.filter(s => s.id !== sourceToDelete.id));
      
      showSuccessNotification(addNotification, 'Source deleted successfully');
    } catch (err) {
      showErrorNotification(addNotification, err, 'Deleting Source');
    } finally {
      setDeletingSource(null);
      setShowDeleteModal(false);
      setSourceToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setShowDeleteModal(false);
    setSourceToDelete(null);
  };

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

  const getSourceTypeLabel = (sourceType: string) => {
    switch (sourceType) {
      case 'document':
        return 'Document';
      case 'url':
        return 'URL';
      case 'video':
        return 'Video';
      case 'image':
        return 'Image';
      case 'text':
        return 'Text';
      default:
        return sourceType;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  /**
   * Get the appropriate badge for notebook count display
   * @param notebookCount - Number of notebooks the source is linked to
   * @returns JSX element for the notebook count badge
   */
  const getNotebookCountBadge = (notebookCount: number | undefined) => {
    if (notebookCount === undefined) return null;
    
    if (notebookCount > 0) {
      return (
        <Badge variant="outline" className="text-blue-600 border-blue-200 bg-blue-50">
          📚 {notebookCount} notebook{notebookCount !== 1 ? 's' : ''}
        </Badge>
      );
    }
    
    return (
      <Badge variant="outline" className="text-gray-500 border-gray-200 bg-gray-50">
        📚 Not linked
      </Badge>
    );
  };

  /**
   * Get the impact message for delete confirmation
   * @param source - Source object to get impact message for
   * @returns Formatted impact message
   */
  const getDeleteImpactMessage = (source: Source) => {
    const baseMessage = `Are you sure you want to delete "${source.title}"?`;
    
    if (source.notebook_count && source.notebook_count > 0) {
      return `${baseMessage}\n\n⚠️ This source is currently linked to ${source.notebook_count} notebook${source.notebook_count !== 1 ? 's' : ''}. Deleting it will remove it from all notebooks.\n\nThis action cannot be undone.`;
    }
    
    return `${baseMessage}\n\nThis source is not currently linked to any notebooks.\n\nThis action cannot be undone.`;
  };

  // Check if any sources are still processing
  const hasProcessingSources = sources.some(source => 
    source.status === 'pending' || source.status === 'processing'
  );

  // Start/stop polling based on processing status
  useEffect(() => {
    if (hasProcessingSources) {
      // Start polling every 3 seconds for sources that are processing
      const interval = setInterval(() => {
        loadSources();
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
    loadSources();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Error Loading Sources</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={() => loadSources()}>Retry</Button>
        </div>
      </div>
    );
  }

  // Calculate stats
  const totalSources = sources.length;
  const urlSources = sources.filter(s => s.source_type === 'url').length;
  const documentSources = sources.filter(s => s.source_type === 'document').length;
  const readySources = sources.filter(s => s.status === 'indexed').length;

  return (
    <div className="container mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-3">
          <Briefcase className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Source Manager</h1>
            <p className="text-gray-600">Manage your information sources</p>
          </div>
        </div>
        <Button 
          className="flex items-center space-x-2"
          onClick={() => setShowCreateModal(true)}
        >
          <Plus className="h-4 w-4" />
          <span>Add Source</span>
        </Button>
      </div>

      {/* Compact Stats Bar */}
      <div className="flex items-center justify-between mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <Briefcase className="h-5 w-5 text-blue-600" />
            <span className="text-sm text-gray-600">Total:</span>
            <span className="font-semibold text-gray-900">{totalSources}</span>
              </div>
          <div className="flex items-center space-x-2">
            <Globe className="h-5 w-5 text-green-600" />
            <span className="text-sm text-gray-600">URLs:</span>
            <span className="font-semibold text-gray-900">{urlSources}</span>
            </div>
          <div className="flex items-center space-x-2">
            <FileText className="h-5 w-5 text-purple-600" />
            <span className="text-sm text-gray-600">Documents:</span>
            <span className="font-semibold text-gray-900">{documentSources}</span>
              </div>
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <span className="text-sm text-gray-600">Ready:</span>
            <span className="font-semibold text-gray-900">{readySources}</span>
              </div>
            </div>
      </div>

      {/* Sources List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">All Sources</h2>
          {isRefreshing && (
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Refreshing...</span>
            </div>
          )}
        </div>
        
        {sources.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Briefcase className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No sources yet</h3>
              <p className="text-gray-600 mb-4">
                Start by adding sources to your notebooks. They'll appear here for management.
              </p>
              <Button onClick={() => setShowCreateModal(true)}>Add Your First Source</Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-3">
            {sources.map((source) => (
              <Card key={source.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        {getSourceIcon(source.source_type)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="text-base font-medium text-gray-900 truncate">
                          {source.title}
                        </h3>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge variant="secondary" className="text-xs">
                            {getSourceTypeLabel(source.source_type)}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            Added {formatDate(source.created_at)}
                          </span>
                          {getNotebookCountBadge(source.notebook_count)}
                          <div className="flex items-center space-x-1">
                            {getStatusIcon(source.status)}
                            <Badge variant={getStatusBadgeVariant(source.status)} className="text-xs">
                              {getStatusText(source.status)}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex-shrink-0">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteClick(source)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={showDeleteModal}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Delete Source"
        message={
          sourceToDelete
            ? getDeleteImpactMessage(sourceToDelete)
            : ''
        }
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={deletingSource !== null}
      />

      {/* Create Source Modal */}
      <CreateSourceModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSourceCreated={() => {
          setShowCreateModal(false);
          // Refresh sources immediately and then again after a short delay
          loadSources(true);
          setTimeout(() => loadSources(true), 1000);
        }}
      />
    </div>
  );
} 