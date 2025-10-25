/**
 * API Service
 * Handles all API calls to the Facebook Checker REST API
 */

import {
    HealthResponse,
    StatusResponse,
    ProxyConfig,
    JobCreateRequest,
    JobCreateResponse,
    JobStatusResponse,
    JobResultsResponse,
    JobLogsResponse,
    JobStreamEvent,
    ApiResponse,
    LicenseValidateResponse,
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
            mode: "cors", // Explicitly set CORS mode
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
                ...options?.headers,
            },
            // Don't include credentials since we don't use authentication
            credentials: "omit",
        });

        if (!response.ok) {
            let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.json();
                console.error("API Error Response:", errorData);
                errorDetail = errorData.detail || errorDetail;

                // If it's a validation error, provide more details
                if (response.status === 422 && errorData.detail && Array.isArray(errorData.detail)) {
                    const validationErrors = errorData.detail
                        .map((err: {loc: string[]; msg: string}) => `${err.loc.join(".")}: ${err.msg}`)
                        .join(", ");
                    errorDetail = `Validation Error: ${validationErrors}`;
                }
            } catch (e) {
                // If error response isn't JSON, use the status text
                console.error("Failed to parse error response:", e);
            }

            return {
                success: false,
                error: errorDetail,
            };
        }

        const data = await response.json();
        return {
            success: true,
            data,
        };
    } catch (error) {
        console.error("Fetch error:", error);
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

// ============================================================================
// License API
// ============================================================================

/**
 * Validate license key
 */
export async function validateLicense(licenseKey: string): Promise<ApiResponse<LicenseValidateResponse>> {
    return fetchApi<LicenseValidateResponse>(API_ENDPOINTS.LICENSE_VALIDATE, {
        method: "POST",
        body: JSON.stringify({license_key: licenseKey}),
    });
}

// ============================================================================
// Jobs API (Current Job Management Only)
// ============================================================================

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

    eventSource.onerror = (error) => {
        console.warn("SSE connection error, will fallback to polling:", error);
        if (onError) {
            onError(new Error("SSE connection failed - using polling fallback"));
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
