/**
 * TypeScript types for Facebook Checker REST API
 */

// ============================================================================
// System Types
// ============================================================================

export interface HealthResponse {
    status: string;
    service: string;
    timestamp: string;
}

export interface StatusResponse {
    active_jobs: number;
}

// ============================================================================
// Proxy Types
// ============================================================================

export interface ProxyConfig {
    enabled: boolean;
    server: string;
    port: number;
    username?: string;
    password?: string;
}

export interface ProxyTestResponse {
    success: boolean;
    message: string;
    ip?: string;
    location?: string;
}

// ============================================================================
// Job Types
// ============================================================================

export type JobStatus = "pending" | "running" | "completed" | "stopped" | "error";

export interface JobCreateRequest {
    phone_numbers: string[];
    workers: number;
    headless: boolean;
}

export interface JobCreateResponse {
    success: boolean;
    job_id: string;
    message: string;
    job: {
        job_id: string;
        status: JobStatus;
        total_numbers: number;
        workers: number;
        headless: boolean;
    };
}

export interface Job {
    job_id: string;
    status: JobStatus;
    total_numbers: number;
    processed_count: number;
    successful_count: number;
    failed_count: number;
    successful_numbers: string[];
    failed_numbers: string[];
    results: PhoneResult[];
    logs: string[];
    workers: number;
    headless: boolean;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    error_message?: string;
}

export interface JobStatusResponse {
    success: boolean;
    job_id: string;
    status: JobStatus;
    total_numbers: number;
    processed_count: number;
    successful_count: number;
    failed_count: number;
}

export interface PhoneResult {
    phone: string;
    status: "success" | "failed";
    message: string;
}

export interface JobResultsResponse {
    success: boolean;
    job_id: string;
    results: PhoneResult[];
    successful_numbers: string[];
    failed_numbers: string[];
    successful_count: number;
    failed_count: number;
}

export interface JobLogsResponse {
    success: boolean;
    job_id: string;
    logs: string[];
}

export interface JobStreamEvent {
    status: JobStatus;
    processed_count: number;
    total_numbers: number;
    successful_count: number;
    failed_count: number;
}

// ============================================================================
// Error Response
// ============================================================================

export interface ApiError {
    detail: string;
}

// ============================================================================
// API Response Wrapper
// ============================================================================

export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
}
