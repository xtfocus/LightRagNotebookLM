'use client';

import React, { useState, useCallback } from 'react';
import { X, Upload, Link, FileText, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { showErrorNotification, showSuccessNotification } from '@/lib/error-handling';
import { useNotifications } from '@/components/ui/NotificationContext';
import { createSource } from '@/components/actions/sources-action';

interface CreateSourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSourceCreated: () => void;
}

interface UploadStatus {
  file: File;
  status: 'uploading' | 'success' | 'error';
  message?: string;
}

interface UrlStatus {
  status: 'processing' | 'success' | 'error';
  url?: string;
  message?: string;
}

export function CreateSourceModal({
  isOpen,
  onClose,
  onSourceCreated
}: CreateSourceModalProps) {
  const [activeTab, setActiveTab] = useState<'files' | 'link'>('files');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [urlInput, setUrlInput] = useState('');
  const [urlTitle, setUrlTitle] = useState('');
  const [urlDescription, setUrlDescription] = useState('');
  const [uploadStatuses, setUploadStatuses] = useState<UploadStatus[]>([]);
  const [urlStatus, setUrlStatus] = useState<UrlStatus | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const { addNotification } = useNotifications();

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setSelectedFiles(files);
  }, []);

  const handleFileDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    setSelectedFiles(files);
  }, []);

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
      // Close modal immediately and notify parent
      onClose();
      onSourceCreated();

      // Use client-side upload function
      const { uploadFilesClient } = await import('@/lib/upload-utils');
      const result = await uploadFilesClient(selectedFiles);

      // Create sources for successful uploads
      const successfulDocuments = result.documents || [];
      for (const document of successfulDocuments) {
        try {
          // Create source for the document
          await createSource({
            title: document.filename,
            source_type: 'document',
            source_metadata: {
              document_id: document.id,
              filename: document.filename,
              mime_type: document.mime_type,
              size: document.size
            }
          });
        } catch (error) {
          console.error('Error creating source for document:', error);
          showErrorNotification(addNotification, error, 'Creating Document Source');
        }
      }

      showSuccessNotification(addNotification, 'Sources created successfully');

    } catch (error) {
      console.error('Upload error:', error);
      showErrorNotification(addNotification, error, 'Creating Sources');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUrlSubmit = async () => {
    if (!urlInput.trim()) return;

    setIsProcessing(true);
    setUrlStatus({ status: 'processing', url: urlInput });

    try {
      // Close modal immediately and notify parent
      onClose();
      onSourceCreated();

      // Create URL source
      await createSource({
        title: urlTitle.trim() || urlInput,
        description: urlDescription.trim() || undefined,
        source_type: 'url',
        source_metadata: {
          url: urlInput.trim()
        }
      });

      showSuccessNotification(addNotification, 'URL source created successfully');

    } catch (error) {
      console.error('URL source creation error:', error);
      showErrorNotification(addNotification, error, 'Creating URL Source');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClose = () => {
    if (!isProcessing) {
      onClose();
      // Reset all form state
      setSelectedFiles([]);
      setUploadStatuses([]);
      setUrlInput('');
      setUrlTitle('');
      setUrlDescription('');
      setUrlStatus(null);
      setActiveTab('files');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Create Source</h2>
            <p className="text-sm text-gray-600 mt-1">
              Add a new source to your collection. Sources can be files or URLs.
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClose}
            disabled={isProcessing}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('files')}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'files'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center justify-center space-x-2">
              <Upload className="h-4 w-4" />
              <span>Files</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('link')}
            className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'link'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center justify-center space-x-2">
              <Link className="h-4 w-4" />
              <span>URL</span>
            </div>
          </button>
        </div>

        {/* File Upload Tab */}
        {activeTab === 'files' && (
          <div className="space-y-4">
            {/* File Drop Zone */}
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                selectedFiles.length > 0
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDrop={handleFileDrop}
              onDragOver={handleDragOver}
            >
              <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600 mb-2">
                Drag and drop files here, or{' '}
                <label className="text-blue-600 hover:text-blue-700 cursor-pointer">
                  browse
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.docx,.txt"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </label>
              </p>
              <p className="text-xs text-gray-500">
                Supported formats: PDF, DOCX, TXT (max 10MB each)
              </p>
            </div>

            {/* Selected Files */}
            {selectedFiles.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">Selected Files</h4>
                {selectedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center space-x-2">
                      <FileText className="h-4 w-4 text-gray-500" />
                      <span className="text-sm text-gray-700">{file.name}</span>
                      <span className="text-xs text-gray-500">
                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(index)}
                      className="h-6 w-6 p-0 text-gray-500 hover:text-red-500"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* Upload Status */}
            {uploadStatuses.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">Upload Status</h4>
                {uploadStatuses.map((status, index) => (
                  <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                    {status.status === 'uploading' && (
                      <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
                    )}
                    {status.status === 'success' && (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    {status.status === 'error' && (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className="text-sm text-gray-700">{status.file.name}</span>
                    {status.message && (
                      <span className={`text-xs ${
                        status.status === 'success' ? 'text-green-600' :
                        status.status === 'error' ? 'text-red-600' :
                        'text-blue-600'
                      }`}>
                        {status.message}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Upload Button */}
            <Button
              onClick={handleFileUpload}
              disabled={selectedFiles.length === 0 || isProcessing}
              className="w-full"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating Sources...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Create Sources
                </>
              )}
            </Button>
          </div>
        )}

        {/* URL Tab */}
        {activeTab === 'link' && (
          <div className="space-y-4">
            {/* URL Input */}
            <div>
              <Label htmlFor="url" className="text-sm font-medium text-gray-700">
                URL *
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
                placeholder="Article title or description"
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
                  Creating Source...
                </>
              ) : (
                <>
                  <Link className="h-4 w-4 mr-2" />
                  Create Source
                </>
              )}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
} 