// API Service for Facebook Checker
import {
  HealthResponse,
  SystemStatus,
  ProxyConfig,
  ProxyTestResponse,
  CreateJobRequest,
  Job,
  JobStatus,
  JobResult,
  JobLog,
} from '@/types/api';

const API_BASE_URL = 'http://localhost:8000/api';

class APIService {
  // System endpoints
  async getHealth(): Promise<HealthResponse> {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) throw new Error('Failed to fetch health status');
    return response.json();
  }

  async getStatus(): Promise<SystemStatus> {
    const response = await fetch(`${API_BASE_URL}/status`);
    if (!response.ok) throw new Error('Failed to fetch system status');
    return response.json();
  }

  // Proxy endpoints
  async getProxyConfig(): Promise<ProxyConfig> {
    const response = await fetch(`${API_BASE_URL}/proxy/config`);
    if (!response.ok) throw new Error('Failed to fetch proxy config');
    return response.json();
  }

  async setProxyConfig(config: ProxyConfig): Promise<ProxyConfig> {
    const response = await fetch(`${API_BASE_URL}/proxy/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!response.ok) throw new Error('Failed to set proxy config');
    return response.json();
  }

  async testProxy(): Promise<ProxyTestResponse> {
    const response = await fetch(`${API_BASE_URL}/proxy/test`);
    if (!response.ok) throw new Error('Failed to test proxy');
    return response.json();
  }

  // Job endpoints
  async listJobs(): Promise<Job[]> {
    const response = await fetch(`${API_BASE_URL}/jobs`);
    if (!response.ok) throw new Error('Failed to fetch jobs');
    return response.json();
  }

  async createJob(request: CreateJobRequest): Promise<Job> {
    const response = await fetch(`${API_BASE_URL}/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create job');
    }
    return response.json();
  }

  async getJob(jobId: string): Promise<Job> {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch job');
    return response.json();
  }

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/status`);
    if (!response.ok) throw new Error('Failed to fetch job status');
    return response.json();
  }

  async getJobResults(jobId: string): Promise<JobResult[]> {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/results`);
    if (!response.ok) throw new Error('Failed to fetch job results');
    return response.json();
  }

  async getJobLogs(jobId: string): Promise<JobLog[]> {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/logs`);
    if (!response.ok) throw new Error('Failed to fetch job logs');
    return response.json();
  }

  async stopJob(jobId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/stop`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to stop job');
    return response.json();
  }

  async deleteJob(jobId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete job');
    return response.json();
  }

  // Stream endpoint (returns EventSource)
  streamJobProgress(jobId: string): EventSource {
    return new EventSource(`${API_BASE_URL}/jobs/${jobId}/stream`);
  }
}

export const apiService = new APIService();

