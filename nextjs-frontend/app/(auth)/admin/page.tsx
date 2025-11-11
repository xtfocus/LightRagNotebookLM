"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, XCircle, Clock, Trash2, Database, HardDrive, AlertTriangle, Play, Eye } from "lucide-react";
import { getRedirectPath } from "@/lib/redirects";
// Removed OpenAPI client imports - using direct API routes instead

interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_approved: boolean;
  is_active: boolean;
  is_superuser: boolean;
  created_at?: string;
}

// Interface for cleanup operation results
interface CleanupOperationResult {
  message: string;
  deleted_count: number;
  total_size?: number;
  failed_deletions?: Array<{
    object_key?: string;
    document_id?: string;
    error: string;
  }>;
  orphaned_files?: Array<{
    object_key: string;
    size: number;
    last_modified: string;
    bucket: string;
  }>;
  orphaned_records?: Array<{
    document_id: string;
    filename: string;
    mime_type: string;
    size: number;
  }>;
}

// Interface for full cleanup results
interface FullCleanupResult {
  consistency_report: {
    is_consistent: boolean;
    orphaned_files: any[];
    orphaned_records: any[];
  };
  minio_cleanup: CleanupOperationResult;
  database_cleanup: CleanupOperationResult;
  dry_run: boolean;
}

// Interface for cleanup operation status
interface CleanupOperationStatus {
  isRunning: boolean;
  result: CleanupOperationResult | FullCleanupResult | null;
  error: string | null;
}

export default function AdminDashboardPage() {
  // User management state
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const router = useRouter();

  // Cleanup operations state - each operation has its own status tracking
  const [orphanedFilesCleanupStatus, setOrphanedFilesCleanupStatus] = useState<CleanupOperationStatus>({
    isRunning: false,
    result: null,
    error: null
  });

  const [orphanedRecordsCleanupStatus, setOrphanedRecordsCleanupStatus] = useState<CleanupOperationStatus>({
    isRunning: false,
    result: null,
    error: null
  });

  const [fullSystemCleanupStatus, setFullSystemCleanupStatus] = useState<CleanupOperationStatus>({
    isRunning: false,
    result: null,
    error: null
  });

  useEffect(() => {
    checkAdminAccess();
  }, []); // Empty dependency array ensures this only runs once

  const checkAdminAccess = async () => {
    try {
      // Get the access token from cookies
      const token = document.cookie
        .split('; ')
        .find(row => row.startsWith('accessToken='))
        ?.split('=')[1];

      if (!token) {
        router.push(getRedirectPath('LOGIN'));
        return;
      }

      const response = await fetch("/api/users/me", {
        headers: {
          "Content-Type": "application/json",
          authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        router.push(getRedirectPath('LOGIN'));
        return;
      }

      const userData = await response.json();
      setCurrentUser(userData);

      // Check if user is a superuser
      if (!userData.is_superuser) {
        router.push(getRedirectPath('DASHBOARD'));
        return;
      }

      // If admin access is confirmed, fetch waitlist users
      await fetchWaitlistUsers();
    } catch (err) {
      console.error("Error checking admin access:", err);
      router.push(getRedirectPath('LOGIN'));
    }
  };

  const fetchWaitlistUsers = async () => {
    try {
      setLoading(true);
      // Get the access token from cookies
      const token = document.cookie
        .split('; ')
        .find(row => row.startsWith('accessToken='))
        ?.split('=')[1];

      const response = await fetch("/api/users/waitlist", {
        headers: {
          "Content-Type": "application/json",
          ...(token && { authorization: `Bearer ${token}` }),
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch waitlist users");
      }

      const data = await response.json();
      setUsers(data.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const approveUser = async (userId: string) => {
    try {
      // Get the access token from cookies
      const token = document.cookie
        .split('; ')
        .find(row => row.startsWith('accessToken='))
        ?.split('=')[1];

      const response = await fetch(`/api/users/${userId}/approve`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(token && { authorization: `Bearer ${token}` }),
        },
      });

      if (!response.ok) {
        throw new Error("Failed to approve user");
      }

      // Refresh the waitlist
      await fetchWaitlistUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve user");
    }
  };

  const rejectUser = async (userId: string) => {
    if (!confirm("Are you sure you want to reject this user? This action cannot be undone.")) {
      return;
    }

    try {
      // Get the access token from cookies
      const token = document.cookie
        .split('; ')
        .find(row => row.startsWith('accessToken='))
        ?.split('=')[1];

      const response = await fetch(`/api/users/${userId}/reject`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(token && { authorization: `Bearer ${token}` }),
        },
      });

      if (!response.ok) {
        throw new Error("Failed to reject user");
      }

      // Refresh the waitlist
      await fetchWaitlistUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reject user");
    }
  };

  // ============================================================================
  // CLEANUP OPERATIONS FUNCTIONS
  // ============================================================================

  /**
   * Helper function to execute cleanup operations with common logic
   * 
   * This function consolidates the common pattern used by all cleanup operations:
   * 1. Set loading state
   * 2. Extract auth token from cookies
   * 3. Make API call with proper headers
   * 4. Handle response and update state
   * 5. Handle errors consistently
   * 
   * @param endpoint - The API endpoint to call (e.g., "/api/uploads/cleanup/orphaned-files")
   * @param operationName - Human-readable name for error messages (e.g., "cleanup orphaned files")
   * @param setStatus - React state setter for the specific cleanup operation's status
   * @param isDryRun - If true, only preview what would be cleaned without actually cleaning
   * 
   * @example
   * ```typescript
   * await executeCleanupOperation(
   *   "/api/uploads/cleanup/orphaned-files",
   *   "cleanup orphaned files",
   *   setOrphanedFilesCleanupStatus,
   *   true // dry run
   * );
   * ```
   */
  const executeCleanupOperation = async (
    endpoint: string,
    operationName: string,
    setStatus: React.Dispatch<React.SetStateAction<CleanupOperationStatus>>,
    isDryRun: boolean = true
  ) => {
    try {
      // Step 1: Set loading state to show user that operation is in progress
      setStatus({
        isRunning: true,
        result: null,
        error: null
      });

      // Step 2: Extract authentication token from browser cookies
      // The token is set during login and contains the user's session information
      const token = document.cookie
        .split('; ')
        .find(row => row.startsWith('accessToken='))
        ?.split('=')[1];

      // Step 3: Make API call to the backend cleanup endpoint
      // The endpoint is a Next.js API route that proxies to the FastAPI backend
      const response = await fetch(`${endpoint}?dry_run=${isDryRun}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Include authorization header if token exists
          ...(token && { authorization: `Bearer ${token}` }),
        },
      });

      // Step 4: Handle API response
      if (!response.ok) {
        // Try to extract error message from response, fallback to generic message
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed to ${operationName}`);
      }

      // Parse successful response
      const data = await response.json();

      // Step 5: Update state with successful result
      setStatus({
        isRunning: false,
        result: data.result, // Backend returns result in data.result
        error: null
      });

    } catch (cleanupError) {
      // Step 6: Handle any errors that occurred during the operation
      // This includes network errors, API errors, and unexpected errors
      const errorMessage = cleanupError instanceof Error 
        ? cleanupError.message 
        : "Unknown error occurred during cleanup";
      
      // Update state with error information
      setStatus({
        isRunning: false,
        result: null,
        error: errorMessage
      });
    }
  };

  /**
   * Execute orphaned files cleanup operation
   * 
   * This operation scans MinIO object storage and removes files that don't have 
   * corresponding database records. These orphaned files typically result from 
   * failed upload transactions where MinIO files were created but database 
   * records failed to commit.
   * 
   * @param isDryRun - If true, only preview what would be cleaned without actually cleaning
   */
  const executeOrphanedFilesCleanup = async (isDryRun: boolean = true) => {
    await executeCleanupOperation(
      "/api/uploads/cleanup/orphaned-files",
      "cleanup orphaned files",
      setOrphanedFilesCleanupStatus,
      isDryRun
    );
  };

  /**
   * Execute orphaned database records cleanup operation
   * 
   * This operation scans the PostgreSQL Document table and removes records that 
   * don't have corresponding MinIO files. These orphaned records typically result 
   * from failed deletion transactions where database records remain after MinIO cleanup.
   * 
   * @param isDryRun - If true, only preview what would be cleaned without actually cleaning
   */
  const executeOrphanedRecordsCleanup = async (isDryRun: boolean = true) => {
    await executeCleanupOperation(
      "/api/uploads/cleanup/orphaned-records",
      "cleanup orphaned records",
      setOrphanedRecordsCleanupStatus,
      isDryRun
    );
  };

  /**
   * Execute full system cleanup operation
   * 
   * This operation performs comprehensive data consistency verification and cleanup 
   * across the entire storage stack (MinIO, PostgreSQL, and Qdrant). It identifies 
   * and resolves inconsistencies in all three storage layers.
   * 
   * @param isDryRun - If true, only preview what would be cleaned without actually cleaning
   */
  const executeFullSystemCleanup = async (isDryRun: boolean = true) => {
    await executeCleanupOperation(
      "/api/uploads/cleanup/full",
      "run full cleanup",
      setFullSystemCleanupStatus,
      isDryRun
    );
  };

  /**
   * Clear cleanup operation results and errors
   * 
   * This function resets the state for a specific cleanup operation, clearing
   * any previous results, errors, or loading states. This allows users to
   * run the same operation again or start fresh.
   * 
   * @param cleanupType - Type of cleanup operation to clear ('files', 'records', or 'full')
   */
  const clearCleanupOperationResult = (cleanupType: 'files' | 'records' | 'full') => {
    switch (cleanupType) {
      case 'files':
        setOrphanedFilesCleanupStatus({
          isRunning: false,
          result: null,
          error: null
        });
        break;
      case 'records':
        setOrphanedRecordsCleanupStatus({
          isRunning: false,
          result: null,
          error: null
        });
        break;
      case 'full':
        setFullSystemCleanupStatus({
          isRunning: false,
          result: null,
          error: null
        });
        break;
    }
  };

  // Show loading while checking admin access
  if (loading || !currentUser) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
        <p className="text-gray-600">Manage user approvals and system access</p>
        <p className="text-sm text-gray-500 mt-2">
          Logged in as: {currentUser.email}
        </p>
      </div>

      <div className="grid gap-6">
        {/* User Management Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              User Waitlist ({users.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {users.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Clock className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No users are currently waiting for approval</p>
              </div>
            ) : (
              <div className="space-y-4">
                {users.map((user) => (
                  <div
                    key={user.id}
                    className="border rounded-lg p-4 flex items-center justify-between"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold">{user.email}</h3>
                        <Badge variant="secondary">Pending</Badge>
                      </div>
                      {user.full_name && (
                        <p className="text-sm text-gray-600">{user.full_name}</p>
                      )}
                      {user.created_at && (
                        <p className="text-xs text-gray-500">
                          Registered: {new Date(user.created_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => approveUser(user.id)}
                        size="sm"
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Approve
                      </Button>
                      <Button
                        onClick={() => rejectUser(user.id)}
                        size="sm"
                        variant="destructive"
                      >
                        <XCircle className="h-4 w-4 mr-1" />
                        Reject
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* System Maintenance Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trash2 className="h-5 w-5" />
              System Maintenance
            </CardTitle>
            <p className="text-sm text-gray-600">
              Clean up orphaned files and database records to maintain system health
            </p>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6">
              {/* Orphaned Files Cleanup */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <HardDrive className="h-5 w-5 text-blue-600" />
                  <h3 className="font-semibold">Orphaned Files Cleanup</h3>
                </div>
                <div className="text-sm text-gray-600 mb-4">
                  <p className="mb-2">Scan MinIO object storage and remove orphaned files:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Cross-reference MinIO object keys with PostgreSQL Document records</li>
                    <li>Identify files from failed upload transactions (MinIO created, DB failed)</li>
                    <li>Remove orphaned objects using MinIO remove_object() API with retry logic</li>
                    <li>Supports dry-run mode for safe preview before deletion</li>
                  </ul>
                </div>
                
                <div className="flex gap-2 mb-4">
                  <Button
                    onClick={() => executeOrphanedFilesCleanup(true)}
                    disabled={orphanedFilesCleanupStatus.isRunning}
                    size="sm"
                    variant="outline"
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    Preview Cleanup
                  </Button>
                  <Button
                    onClick={() => executeOrphanedFilesCleanup(false)}
                    disabled={orphanedFilesCleanupStatus.isRunning}
                    size="sm"
                    variant="destructive"
                  >
                    <Play className="h-4 w-4 mr-1" />
                    Execute Cleanup
                  </Button>
                  {orphanedFilesCleanupStatus.result && (
                    <Button
                      onClick={() => clearCleanupOperationResult('files')}
                      size="sm"
                      variant="ghost"
                    >
                      Clear Results
                    </Button>
                  )}
                </div>

                {/* Orphaned Files Cleanup Results */}
                {orphanedFilesCleanupStatus.isRunning && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-blue-800 text-sm">Running orphaned files cleanup...</p>
                  </div>
                )}

                {orphanedFilesCleanupStatus.error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-red-800 text-sm">Error: {orphanedFilesCleanupStatus.error}</p>
                  </div>
                )}

                {orphanedFilesCleanupStatus.result && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-green-800 text-sm font-medium">
                      {(orphanedFilesCleanupStatus.result as CleanupOperationResult).message}
                    </p>
                    {(orphanedFilesCleanupStatus.result as CleanupOperationResult).deleted_count > 0 && (
                      <p className="text-green-700 text-sm mt-1">
                        Deleted: {(orphanedFilesCleanupStatus.result as CleanupOperationResult).deleted_count} files
                        {(orphanedFilesCleanupStatus.result as CleanupOperationResult).total_size && (
                          <span> ({Math.round((orphanedFilesCleanupStatus.result as CleanupOperationResult).total_size! / 1024 / 1024)} MB)</span>
                        )}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Orphaned Records Cleanup */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Database className="h-5 w-5 text-purple-600" />
                  <h3 className="font-semibold">Orphaned Records Cleanup</h3>
                </div>
                <div className="text-sm text-gray-600 mb-4">
                  <p className="mb-2">Scan PostgreSQL Document table and remove orphaned records:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Cross-reference Document.object_key with MinIO object existence (stat_object check)</li>
                    <li>Identify records from failed deletion transactions (DB record remains, MinIO deleted)</li>
                    <li>Remove orphaned records using SQLModel delete operations with transactional safety</li>
                    <li>Supports dry-run mode for safe preview before deletion</li>
                  </ul>
                </div>
                
                <div className="flex gap-2 mb-4">
                  <Button
                    onClick={() => executeOrphanedRecordsCleanup(true)}
                    disabled={orphanedRecordsCleanupStatus.isRunning}
                    size="sm"
                    variant="outline"
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    Preview Cleanup
                  </Button>
                  <Button
                    onClick={() => executeOrphanedRecordsCleanup(false)}
                    disabled={orphanedRecordsCleanupStatus.isRunning}
                    size="sm"
                    variant="destructive"
                  >
                    <Play className="h-4 w-4 mr-1" />
                    Execute Cleanup
                  </Button>
                  {orphanedRecordsCleanupStatus.result && (
                    <Button
                      onClick={() => clearCleanupOperationResult('records')}
                      size="sm"
                      variant="ghost"
                    >
                      Clear Results
                    </Button>
                  )}
                </div>

                {/* Orphaned Records Cleanup Results */}
                {orphanedRecordsCleanupStatus.isRunning && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-blue-800 text-sm">Running orphaned records cleanup...</p>
                  </div>
                )}

                {orphanedRecordsCleanupStatus.error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-red-800 text-sm">Error: {orphanedRecordsCleanupStatus.error}</p>
                  </div>
                )}

                {orphanedRecordsCleanupStatus.result && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-green-800 text-sm font-medium">
                      {(orphanedRecordsCleanupStatus.result as CleanupOperationResult).message}
                    </p>
                    {(orphanedRecordsCleanupStatus.result as CleanupOperationResult).deleted_count > 0 && (
                      <p className="text-green-700 text-sm mt-1">
                        Deleted: {(orphanedRecordsCleanupStatus.result as CleanupOperationResult).deleted_count} records
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Full System Cleanup */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="h-5 w-5 text-orange-600" />
                  <h3 className="font-semibold">Full System Cleanup</h3>
                </div>
                <div className="text-sm text-gray-600 mb-4">
                  <p className="mb-2">Execute comprehensive data consistency verification and cleanup:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Cross-reference analysis between MinIO, PostgreSQL, and Qdrant storage layers</li>
                    <li>Identify inconsistencies in object storage, metadata, and vector embeddings</li>
                    <li>Resolve orphaned files, database records, and vector chunks</li>
                    <li>Generate detailed consistency report with dry-run mode support</li>
                  </ul>
                </div>
                
                <div className="flex gap-2 mb-4">
                  <Button
                    onClick={() => executeFullSystemCleanup(true)}
                    disabled={fullSystemCleanupStatus.isRunning}
                    size="sm"
                    variant="outline"
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    Preview Full Cleanup
                  </Button>
                  <Button
                    onClick={() => executeFullSystemCleanup(false)}
                    disabled={fullSystemCleanupStatus.isRunning}
                    size="sm"
                    variant="destructive"
                  >
                    <Play className="h-4 w-4 mr-1" />
                    Execute Full Cleanup
                  </Button>
                  {fullSystemCleanupStatus.result && (
                    <Button
                      onClick={() => clearCleanupOperationResult('full')}
                      size="sm"
                      variant="ghost"
                    >
                      Clear Results
                    </Button>
                  )}
                </div>

                {/* Full System Cleanup Results */}
                {fullSystemCleanupStatus.isRunning && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-blue-800 text-sm">Running full system cleanup...</p>
                  </div>
                )}

                {fullSystemCleanupStatus.error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-red-800 text-sm">Error: {fullSystemCleanupStatus.error}</p>
                  </div>
                )}

                {fullSystemCleanupStatus.result && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-green-800 text-sm font-medium">
                      Full system cleanup completed
                    </p>
                    <div className="text-green-700 text-sm mt-2 space-y-1">
                      <p>MinIO Cleanup: {(fullSystemCleanupStatus.result as FullCleanupResult).minio_cleanup.deleted_count} files</p>
                      <p>Database Cleanup: {(fullSystemCleanupStatus.result as FullCleanupResult).database_cleanup.deleted_count} records</p>
                      <p>Data Consistency: {(fullSystemCleanupStatus.result as FullCleanupResult).consistency_report.is_consistent ? 'Consistent' : 'Inconsistent'}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 