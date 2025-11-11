// API Configuration
export const API_CONFIG = {
  // Backend API prefix - defaults to /api/v1 but can be overridden via environment
  BACKEND_API_PREFIX: process.env.NEXT_PUBLIC_BACKEND_API_PREFIX || "/api/v1",
  
  // Agent API prefix - defaults to /api/v1 but can be overridden via environment
  AGENT_API_PREFIX: process.env.NEXT_PUBLIC_AGENT_API_PREFIX || "/api/v1",
  
  // Base URL for backend API
  BACKEND_BASE_URL: process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || "http://backend:8000",
  
  // Base URL for agent API
  AGENT_BASE_URL: process.env.AGENT_URL || "http://agent:8000",
};

// Helper function to build backend API URLs
export const buildBackendUrl = (endpoint: string): string => {
  const baseUrl = API_CONFIG.BACKEND_BASE_URL.replace(/\/$/, '');
  const prefix = API_CONFIG.BACKEND_API_PREFIX.replace(/^\/+|\/+$/g, '');
  const cleanEndpoint = endpoint.replace(/^\/+/, '');
  return `${baseUrl}/${prefix}/${cleanEndpoint}`;
};

// Helper function to build agent API URLs
export const buildAgentUrl = (endpoint: string): string => {
  const baseUrl = API_CONFIG.AGENT_BASE_URL.replace(/\/$/, '');
  const prefix = API_CONFIG.AGENT_API_PREFIX.replace(/^\/+|\/+$/g, '');
  const cleanEndpoint = endpoint.replace(/^\/+/, '');
  return `${baseUrl}/${prefix}/${cleanEndpoint}`;
}; 