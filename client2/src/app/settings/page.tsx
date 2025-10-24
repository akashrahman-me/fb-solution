"use client";
import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Grid,
  Alert,
  CircularProgress,
  Divider,
  Card,
  CardContent,
} from '@mui/material';
import { Save, Refresh, CheckCircle } from '@mui/icons-material';
import { toast } from 'react-toastify';
import { apiService } from '@/services/api';
import { ProxyConfig, SystemStatus } from '@/types/api';

export default function SettingsPage() {
  const [proxyConfig, setProxyConfig] = useState<ProxyConfig>({
    enabled: false,
    server: '',
    port: 0,
    username: '',
    password: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const [config, status] = await Promise.all([
        apiService.getProxyConfig(),
        apiService.getStatus(),
      ]);
      setProxyConfig(config);
      setSystemStatus(status);
    } catch (error: any) {
      toast.error(error.message || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleSave = async () => {
    try {
      setSaving(true);
      await apiService.setProxyConfig(proxyConfig);
      toast.success('Proxy settings saved');
    } catch (error: any) {
      toast.error(error.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      const result = await apiService.testProxy();
      if (result.success) {
        toast.success(result.message + (result.ip ? ` (IP: ${result.ip})` : ''));
      } else {
        toast.error(result.message);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to test proxy');
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      {systemStatus && (
        <Alert 
          severity={systemStatus.expired ? 'error' : 'success'} 
          icon={!systemStatus.expired ? <CheckCircle /> : undefined}
          sx={{ mb: 3 }}
        >
          <Typography variant="body1">
            {systemStatus.expiration_message}
          </Typography>
          {systemStatus.active_jobs > 0 && (
            <Typography variant="body2">
              Active Jobs: {systemStatus.active_jobs}
            </Typography>
          )}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Proxy Configuration
        </Typography>
        <Divider sx={{ mb: 3 }} />

        <FormControlLabel
          control={
            <Switch
              checked={proxyConfig.enabled}
              onChange={(e) => setProxyConfig({ ...proxyConfig, enabled: e.target.checked })}
            />
          }
          label="Enable Proxy"
          sx={{ mb: 3 }}
        />

        <Grid container spacing={2}>
          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              label="Proxy Server"
              placeholder="31.59.20.176"
              value={proxyConfig.server}
              onChange={(e) => setProxyConfig({ ...proxyConfig, server: e.target.value })}
              disabled={!proxyConfig.enabled}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              type="number"
              label="Port"
              placeholder="6754"
              value={proxyConfig.port || ''}
              onChange={(e) => setProxyConfig({ ...proxyConfig, port: parseInt(e.target.value) || 0 })}
              disabled={!proxyConfig.enabled}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Username"
              placeholder="proxy_username"
              value={proxyConfig.username}
              onChange={(e) => setProxyConfig({ ...proxyConfig, username: e.target.value })}
              disabled={!proxyConfig.enabled}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="password"
              label="Password"
              placeholder="proxy_password"
              value={proxyConfig.password}
              onChange={(e) => setProxyConfig({ ...proxyConfig, password: e.target.value })}
              disabled={!proxyConfig.enabled}
            />
          </Grid>
        </Grid>

        <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </Button>
          <Button
            variant="outlined"
            startIcon={testing ? <CircularProgress size={20} /> : <Refresh />}
            onClick={handleTest}
            disabled={testing || !proxyConfig.enabled}
          >
            Test Proxy
          </Button>
        </Box>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          System Information
        </Typography>
        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  API Endpoint
                </Typography>
                <Typography variant="body1" fontFamily="monospace">
                  http://localhost:8000
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  API Documentation
                </Typography>
                <Button
                  variant="text"
                  size="small"
                  onClick={() => window.open('http://localhost:8000/docs', '_blank')}
                >
                  Open API Docs
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
}
// API Types for Facebook Checker

export interface HealthResponse {
  status: string;
  service: string;
  timestamp: string;
}

export interface SystemStatus {
  expired: boolean;
  expiration_message: string;
  expiration_date: string;
  active_jobs: number;
}

export interface ProxyConfig {
  enabled: boolean;
  server: string;
  port: number;
  username: string;
  password: string;
}

export interface ProxyTestResponse {
  success: boolean;
  message: string;
  ip?: string;
  country?: string;
}

export interface CreateJobRequest {
  phone_numbers: string[];
  workers: number;
  headless: boolean;
}

export interface JobResult {
  phone_number: string;
  exists: boolean;
  profile_name?: string;
  profile_url?: string;
  error?: string;
}

export interface Job {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'stopped' | 'error';
  phone_numbers: string[];
  workers: number;
  headless: boolean;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  total: number;
  processed: number;
  found: number;
  not_found: number;
  errors: number;
  results: JobResult[];
  error_message?: string;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'stopped' | 'error';
  total: number;
  processed: number;
  found: number;
  not_found: number;
  errors: number;
}

export interface JobLog {
  timestamp: string;
  level: string;
  message: string;
}

export interface StreamUpdate {
  job_id: string;
  status: string;
  processed: number;
  total: number;
  found: number;
  not_found: number;
  errors: number;
  latest_result?: JobResult;
}

