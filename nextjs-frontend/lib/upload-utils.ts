// Client-side upload utilities

export async function uploadFilesClient(files: File[]): Promise<any> {
  try {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    
    // Get auth token from cookies
    const token = await getAuthToken();
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    const url = `${apiBaseUrl}/api/v1/uploads/files/`;
    
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    // Don't set Content-Type for FormData - browser will set it with boundary
    
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('[File Upload] Error:', error);
    throw error;
  }
}

// Utility to extract auth token from cookies (client-side)
async function getAuthToken(): Promise<string | null> {
  // In client-side code, we need to get the token differently
  // For now, we'll try to get it from localStorage or a cookie
  if (typeof window !== 'undefined') {
    // Try to get from localStorage first
    const token = localStorage.getItem('accessToken');
    if (token) return token;
    
    // Try to get from cookies
    const cookies = document.cookie.split(';');
    const tokenCookie = cookies.find(cookie => cookie.trim().startsWith('accessToken='));
    if (tokenCookie) {
      return tokenCookie.split('=')[1];
    }
  }
  
  return null;
} 