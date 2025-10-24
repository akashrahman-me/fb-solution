/**
 * API Configuration
 * Manages base URL and API endpoints for the Facebook Checker REST API
 */

// API base URL - defaults to localhost:8000
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// API endpoints
export const API_ENDPOINTS = {
    // System
    HEALTH: "/api/health",
    STATUS: "/api/status",

    // Proxy
    PROXY_CONFIG: "/api/proxy/config",
    PROXY_TEST: "/api/proxy/test",

    // Jobs (Current Job Management)
    JOBS: "/api/jobs", // POST - create job
    JOB_STATUS: (jobId: string) => `/api/jobs/${jobId}/status`,
    JOB_RESULTS: (jobId: string) => `/api/jobs/${jobId}/results`,
    JOB_LOGS: (jobId: string) => `/api/jobs/${jobId}/logs`,
    JOB_STOP: (jobId: string) => `/api/jobs/${jobId}/stop`,
    JOB_STREAM: (jobId: string) => `/api/jobs/${jobId}/stream`,
} as const;

/**
 * Get full API URL
 */
export function getApiUrl(endpoint: string): string {
    return `${API_BASE_URL}${endpoint}`;
}

/**
 * API request configuration
 */
export const API_CONFIG = {
    timeout: 30000, // 30 seconds
    retries: 3,
    retryDelay: 1000, // 1 second
};
