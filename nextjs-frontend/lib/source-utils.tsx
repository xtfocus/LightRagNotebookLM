import React from 'react';
import { Clock, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

export interface SourceStatus {
  status: 'pending' | 'processing' | 'indexed' | 'failed';
}

/**
 * Get the appropriate icon for a source status
 */
export const getStatusIcon = (status: string): React.ReactElement => {
  switch (status) {
    case 'pending':
      return <Clock className="h-4 w-4 text-yellow-500" />;
    case 'processing':
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
    case 'indexed':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'failed':
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Clock className="h-4 w-4 text-gray-400" />;
  }
};

/**
 * Get the display text for a source status
 */
export const getStatusText = (status: string) => {
  switch (status) {
    case 'pending':
      return 'Pending';
    case 'processing':
      return 'Processing...';
    case 'indexed':
      return 'Ready';
    case 'failed':
      return 'Failed';
    default:
      return 'Unknown';
  }
};

/**
 * Get the badge variant for a source status
 */
export const getStatusBadgeVariant = (status: string) => {
  switch (status) {
    case 'pending':
      return 'secondary';
    case 'processing':
      return 'default';
    case 'indexed':
      return 'default';
    case 'failed':
      return 'destructive';
    default:
      return 'secondary';
  }
};

/**
 * Map backend status to frontend status (for backward compatibility)
 */
export const getSourceStatus = (source: { source: { status: string } }) => {
  // Map backend status to frontend status
  switch (source.source.status) {
    case 'pending':
      return 'pending';
    case 'processing':
      return 'processing';
    case 'indexed':
      return 'ready';
    case 'failed':
      return 'error';
    default:
      return 'pending';
  }
};

/**
 * Get status icon for mapped status (ready/error instead of indexed/failed)
 */
export const getMappedStatusIcon = (status: string): React.ReactElement => {
  switch (status) {
    case 'pending':
      return <Clock className="h-4 w-4 text-yellow-500" />;
    case 'processing':
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
    case 'ready':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'error':
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Clock className="h-4 w-4 text-gray-400" />;
  }
};

/**
 * Get status text for mapped status (ready/error instead of indexed/failed)
 */
export const getMappedStatusText = (status: string) => {
  switch (status) {
    case 'pending':
      return 'Pending';
    case 'processing':
      return 'Processing...';
    case 'ready':
      return 'Ready';
    case 'error':
      return 'Error';
    default:
      return 'Unknown';
  }
}; 