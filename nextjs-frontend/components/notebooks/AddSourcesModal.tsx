'use client';

import React, { useState, useCallback } from 'react';
import { X, Upload, Link, FileText, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { colors, spacing, borderRadius } from '@/lib/design-system';

interface AddSourcesModalProps {
  isOpen: boolean;
  onClose: () => void;
  notebookId: string;
  currentSourceCount: number;
  maxSources: number;
  onSourceAdded: () => void;
}

interface UploadStatus {
  file: File;
  status: 'uploading' | 'success' | 'error';
  message?: string;
}

interface UrlStatus {
  url: string;
  status: 'processing' | 'success' | 'error';
  message?: string;
}

export function AddSourcesModal({
  isOpen,
  onClose,
  notebookId,
  currentSourceCount,
  maxSources,
  onSourceAdded
}: AddSourcesModalProps) {
  const [activeTab, setActiveTab] = useState<'files' | 'link'>('files');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [urlInput, setUrlInput] = useState('');
  const [urlTitle, setUrlTitle] = useState('');
  const [urlDescription, setUrlDescription] = useState('');
  const [uploadStatuses, setUploadStatuses] = useState<UploadStatus[]>([]);
  const [urlStatus, setUrlStatus] = useState<UrlStatus | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const remainingSources = maxSources - currentSourceCount;
  const canAddMore = remainingSources > 0;

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length > remainingSources) {
      alert(`You can only add ${remainingSources} more sources.`);
      return;
    }
    setSelectedFiles(files);
  }, [remainingSources]);

  const handleFileDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    if (files.length > remainingSources) {
      alert(`You can only add ${remainingSources} more sources.`);
      return;
    }
    setSelectedFiles(files);
  }, [remainingSources]);

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  }, []);

  const removeFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  const handleFileUpload = async () => {
    if (selectedFiles.length === 0) return;

    setIsProcessing(true);
    const newUploadStatuses: UploadStatus[] = selectedFiles.map(file => ({
      file,
      status: 'uploading'
    }));
    setUploadStatuses(newUploadStatuses);

    try {
      // Use client-side upload function
      const { uploadFilesClient } = await import('@/lib/upload-utils');
      const result = await uploadFilesClient(selectedFiles);

      // Update statuses based on result
      const updatedStatuses = selectedFiles.map((file, index) => {
        const document = result.documents?.find((doc: any) => doc.filename === file.name);
        if (document) {
          return {
            file,
            status: 'success' as const,
            message: 'Upload successful'
          };
        } else {
          return {
            file,
            status: 'error' as const,
            message: 'Upload failed'
          };
        }
      });
      setUploadStatuses(updatedStatuses);

      // Add successful uploads to notebook
      const successfulDocuments = result.documents || [];
      for (const document of successfulDocuments) {
        try {
          const { createSource, addSourceToNotebook } = await import('@/components/actions/sources-action');
          
          // Create source for the document
          const source = await createSource({
            title: document.filename,
            source_type: 'document',
            source_metadata: {
              document_id: document.id,
              filename: document.filename,
              mime_type: document.mime_type,
              size: document.size
            }
          });

          // Add source to notebook
          await addSourceToNotebook(notebookId, {
            source_id: source.id
          });
        } catch (error) {
          console.error('Error adding document to notebook:', error);
        }
      }

      onSourceAdded();
      // Close modal immediately after successful addition
      onClose();
      setSelectedFiles([]);
      setUploadStatuses([]);

    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatuses(selectedFiles.map(file => ({
        file,
        status: 'error',
        message: 'Upload failed'
      })));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUrlSubmit = async () => {
    if (!urlInput.trim()) return;

    setIsProcessing(true);
    setUrlStatus({
      url: urlInput,
      status: 'processing'
    });

    try {
      const { processUrl, addSourceToNotebook } = await import('@/components/actions/sources-action');
      
      // Process URL and create source
      const source = await processUrl({
        url: urlInput,
        title: urlTitle || urlInput,
        description: urlDescription
      });

      // Add source to notebook
      await addSourceToNotebook(notebookId, {
        source_id: source.id
      });

      setUrlStatus({
        url: urlInput,
        status: 'success',
        message: 'URL processed successfully'
      });

      onSourceAdded();
      // Close modal immediately after successful addition
      onClose();
      setUrlInput('');
      setUrlTitle('');
      setUrlDescription('');
      setUrlStatus(null);

    } catch (error) {
      console.error('URL processing error:', error);
      setUrlStatus({
        url: urlInput,
        status: 'error',
        message: 'Failed to process URL'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Add sources</h2>
            <p className="text-sm text-gray-600 mt-1">
              Sources let AI base its responses on the information that matters most to you.
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            disabled={isProcessing}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Source Limit Indicator */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Source limit</span>
            <span className="text-sm text-gray-500">{currentSourceCount}/{maxSources}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(currentSourceCount / maxSources) * 100}%` }}
            />
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('files')}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'files'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <FileText className="h-4 w-4 inline mr-2" />
            Files
          </button>
          <button
            onClick={() => setActiveTab('link')}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'link'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Link className="h-4 w-4 inline mr-2" />
            Link
          </button>
        </div>

        {/* Content */}
        {activeTab === 'files' && (
          <div className="space-y-4">
            {/* File Drop Zone */}
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                selectedFiles.length > 0
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDrop={handleFileDrop}
              onDragOver={handleDragOver}
            >
              <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p className="text-lg font-medium text-gray-900 mb-2">
                Drop files here or click to browse
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Supported: PDF, DOCX, TXT, MD, CSV, XLSX, XLS, PPT, PPTX
              </p>
              <input
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.txt,.md,.csv,.xlsx,.xls,.ppt,.pptx"
                onChange={handleFileSelect}
                className="hidden"
                id="file-input"
                disabled={!canAddMore}
              />
              <label
                htmlFor="file-input"
                className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md cursor-pointer ${
                  canAddMore
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                Choose Files
              </label>
            </div>

            {/* Selected Files */}
            {selectedFiles.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-900">Selected Files</h3>
                {selectedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <FileText className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{file.name}</p>
                        <p className="text-xs text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {uploadStatuses[index] && (
                        <>
                          {uploadStatuses[index].status === 'uploading' && (
                            <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
                          )}
                          {uploadStatuses[index].status === 'success' && (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          )}
                          {uploadStatuses[index].status === 'error' && (
                            <AlertCircle className="h-4 w-4 text-red-500" />
                          )}
                        </>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(index)}
                        disabled={isProcessing}
                        className="h-6 w-6 p-0"
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Upload Button */}
            {selectedFiles.length > 0 && (
              <Button
                onClick={handleFileUpload}
                disabled={isProcessing}
                className="w-full"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  `Upload ${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''}`
                )}
              </Button>
            )}
          </div>
        )}

        {activeTab === 'link' && (
          <div className="space-y-4">
            {/* URL Input */}
            <div>
              <Label htmlFor="url" className="text-sm font-medium text-gray-700">
                Website URL
              </Label>
              <Input
                id="url"
                type="url"
                placeholder="https://example.com/article"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                disabled={isProcessing}
                className="mt-1"
              />
            </div>

            {/* Optional Title */}
            <div>
              <Label htmlFor="title" className="text-sm font-medium text-gray-700">
                Title (optional)
              </Label>
              <Input
                id="title"
                type="text"
                placeholder="Article title"
                value={urlTitle}
                onChange={(e) => setUrlTitle(e.target.value)}
                disabled={isProcessing}
                className="mt-1"
              />
            </div>

            {/* Optional Description */}
            <div>
              <Label htmlFor="description" className="text-sm font-medium text-gray-700">
                Description (optional)
              </Label>
              <Input
                id="description"
                type="text"
                placeholder="Brief description"
                value={urlDescription}
                onChange={(e) => setUrlDescription(e.target.value)}
                disabled={isProcessing}
                className="mt-1"
              />
            </div>

            {/* URL Status */}
            {urlStatus && (
              <div className={`p-3 rounded-lg ${
                urlStatus.status === 'success' ? 'bg-green-50' :
                urlStatus.status === 'error' ? 'bg-red-50' :
                'bg-blue-50'
              }`}>
                <div className="flex items-center space-x-2">
                  {urlStatus.status === 'processing' && (
                    <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
                  )}
                  {urlStatus.status === 'success' && (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                  {urlStatus.status === 'error' && (
                    <AlertCircle className="h-4 w-4 text-red-500" />
                  )}
                  <span className={`text-sm ${
                    urlStatus.status === 'success' ? 'text-green-800' :
                    urlStatus.status === 'error' ? 'text-red-800' :
                    'text-blue-800'
                  }`}>
                    {urlStatus.message || urlStatus.url}
                  </span>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <Button
              onClick={handleUrlSubmit}
              disabled={!urlInput.trim() || isProcessing}
              className="w-full"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                'Add URL'
              )}
            </Button>
          </div>
        )}

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={isProcessing}
            >
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
} 