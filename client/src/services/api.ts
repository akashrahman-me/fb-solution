/**
 * API Service
 * Handles all API calls to the Facebook Checker REST API
 */

import {
    HealthResponse,
    StatusResponse,
    ProxyConfig,
    ProxyTestResponse,
    JobCreateRequest,
    JobCreateResponse,
    Job,
    JobStatusResponse,
    JobResultsResponse,
    JobLogsResponse,
    JobStreamEvent,
    JobsListResponse,
    JobDetailResponse,
    ApiError,
    ApiResponse,
} from "@/types/api";
import {API_ENDPOINTS, getApiUrl} from "@/config/api";

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    try {
        const response = await fetch(getApiUrl(endpoint), {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...options?.headers,
            },
        });

        if (!response.ok) {
            const error: ApiError = await response.json();
            return {
                success: false,
                error: error.detail || `HTTP ${response.status}: ${response.statusText}`,
            };
        }

        const data = await response.json();
        return {
            success: true,
            data,
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : "Unknown error occurred",
        };
    }
}

// ============================================================================
// System API
// ============================================================================

/**
 * Check API health status
 */
export async function checkHealth(): Promise<ApiResponse<HealthResponse>> {
    return fetchApi<HealthResponse>(API_ENDPOINTS.HEALTH);
}

/**
 * Get system status
 */
export async function getSystemStatus(): Promise<ApiResponse<StatusResponse>> {
    return fetchApi<StatusResponse>(API_ENDPOINTS.STATUS);
}

// ============================================================================
// Proxy API
// ============================================================================

/**
 * Get current proxy configuration
 */
export async function getProxyConfig(): Promise<ApiResponse<ProxyConfig>> {
    return fetchApi<ProxyConfig>(API_ENDPOINTS.PROXY_CONFIG);
}

/**
 * Update proxy configuration
 */
export async function setProxyConfig(config: ProxyConfig): Promise<ApiResponse<ProxyConfig>> {
    return fetchApi<ProxyConfig>(API_ENDPOINTS.PROXY_CONFIG, {
        method: "POST",
        body: JSON.stringify(config),
    });
}

/**
 * Test proxy connection
 */
export async function testProxyConnection(): Promise<ApiResponse<ProxyTestResponse>> {
    return fetchApi<ProxyTestResponse>(API_ENDPOINTS.PROXY_TEST);
}

// ============================================================================
// Jobs API
// ============================================================================

/**
 * Get all jobs
 */
export async function getAllJobs(): Promise<ApiResponse<Job[]>> {
    const response = await fetchApi<JobsListResponse>(API_ENDPOINTS.JOBS);
    if (response.success && response.data) {
        return {
            success: true,
            data: response.data.jobs,
        };
    }
    return {
        success: false,
        error: response.error,
    };
}

/**
 * Create a new job
 */
export async function createJob(request: JobCreateRequest): Promise<ApiResponse<JobCreateResponse>> {
    return fetchApi<JobCreateResponse>(API_ENDPOINTS.JOBS, {
        method: "POST",
        body: JSON.stringify(request),
    });
}

/**
 * Get job details
 */
export async function getJobDetails(jobId: string): Promise<ApiResponse<Job>> {
    const response = await fetchApi<JobDetailResponse>(API_ENDPOINTS.JOB_DETAIL(jobId));
    if (response.success && response.data) {
        return {
            success: true,
            data: response.data.job,
        };
    }
    return {
        success: false,
        error: response.error,
    };
}

/**
 * Get job status (lightweight)
 */
export async function getJobStatus(jobId: string): Promise<ApiResponse<JobStatusResponse>> {
    return fetchApi<JobStatusResponse>(API_ENDPOINTS.JOB_STATUS(jobId));
}

/**
 * Get job results
 */
export async function getJobResults(jobId: string): Promise<ApiResponse<JobResultsResponse>> {
    return fetchApi<JobResultsResponse>(API_ENDPOINTS.JOB_RESULTS(jobId));
}

/**
 * Get job logs
 */
export async function getJobLogs(jobId: string): Promise<ApiResponse<JobLogsResponse>> {
    return fetchApi<JobLogsResponse>(API_ENDPOINTS.JOB_LOGS(jobId));
}

/**
 * Stop a running job
 */
export async function stopJob(jobId: string): Promise<ApiResponse<{message: string}>> {
    return fetchApi<{message: string}>(API_ENDPOINTS.JOB_STOP(jobId), {
        method: "POST",
    });
}

/**
 * Delete a job
 */
export async function deleteJob(jobId: string): Promise<ApiResponse<{message: string}>> {
    return fetchApi<{message: string}>(API_ENDPOINTS.JOB_DETAIL(jobId), {
        method: "DELETE",
    });
}

/**
 * Stream job progress using Server-Sent Events (SSE)
 */
export function streamJobProgress(
    jobId: string,
    onMessage: (event: JobStreamEvent) => void,
    onError?: (error: Error) => void,
    onComplete?: () => void
): EventSource {
    const eventSource = new EventSource(getApiUrl(API_ENDPOINTS.JOB_STREAM(jobId)));

    eventSource.onmessage = (event) => {
        try {
            const data: JobStreamEvent = JSON.parse(event.data);
            onMessage(data);

            // Auto-close on complete, stopped, or error
            if (
                data.status === "completed" ||
                data.status === "stopped" ||
                data.status === "error" ||
                event.data.includes('"status":"done"')
            ) {
                eventSource.close();
                if (onComplete) onComplete();
            }
        } catch (error) {
            if (onError) {
                onError(error instanceof Error ? error : new Error("Failed to parse SSE data"));
            }
        }
    };

    eventSource.onerror = () => {
        if (onError) {
            onError(new Error("EventSource failed"));
        }
        eventSource.close();
    };

    return eventSource;
}

// ============================================================================
// Polling Helper
// ============================================================================

/**
 * Poll job status until completion
 */
export async function pollJobStatus(
    jobId: string,
    onUpdate: (status: JobStatusResponse) => void,
    interval: number = 2000,
    maxAttempts: number = 1000
): Promise<JobStatusResponse> {
    let attempts = 0;

    return new Promise((resolve, reject) => {
        const poll = async () => {
            attempts++;

            if (attempts > maxAttempts) {
                reject(new Error("Polling timeout: maximum attempts reached"));
                return;
            }

            const response = await getJobStatus(jobId);

            if (!response.success || !response.data) {
                reject(new Error(response.error || "Failed to get job status"));
                return;
            }

            const status = response.data;
            onUpdate(status);

            // Check if job is complete
            if (status.status === "completed" || status.status === "stopped" || status.status === "error") {
                resolve(status);
                return;
            }

            // Continue polling
            setTimeout(poll, interval);
        };

        poll();
    });
}
