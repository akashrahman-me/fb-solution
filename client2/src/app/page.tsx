"use client";
import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Button,
  Divider,
  Chip,
} from '@mui/material';
import { CheckCircle, Error, PlayArrow, History, Settings } from '@mui/icons-material';
import { toast } from 'react-toastify';
import { apiService } from '@/services/api';
import { SystemStatus, HealthResponse } from '@/types/api';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const [healthData, statusData] = await Promise.all([
        apiService.getHealth(),
        apiService.getStatus(),
      ]);
      setHealth(healthData);
      setStatus(statusData);
    } catch (error: any) {
      setError(error.message || 'Failed to connect to API server');
      toast.error('Unable to connect to API. Make sure the server is running on http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

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
        Dashboard
      </Typography>

      {error ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="body1" gutterBottom>
            <strong>API Connection Error</strong>
          </Typography>
          <Typography variant="body2" gutterBottom>
            {error}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Please ensure the FastAPI server is running at http://localhost:8000
          </Typography>
          <Button
            variant="outlined"
            size="small"
            onClick={loadStatus}
            sx={{ mt: 2 }}
          >
            Retry Connection
          </Button>
        </Alert>
      ) : (
        <>
          <Alert
            severity={health?.status === 'healthy' ? 'success' : 'error'}
            icon={health?.status === 'healthy' ? <CheckCircle /> : <Error />}
            sx={{ mb: 3 }}
          >
            <Typography variant="body1">
              <strong>{health?.service}</strong>
            </Typography>
            <Typography variant="body2">
              Status: {health?.status?.toUpperCase()} | Last checked: {health?.timestamp ? new Date(health.timestamp).toLocaleString() : 'N/A'}
            </Typography>
          </Alert>

          {status && (
            <Alert
              severity={status.expired ? 'error' : 'info'}
              sx={{ mb: 3 }}
            >
              <Typography variant="body1">
                {status.expiration_message}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Expiration: {new Date(status.expiration_date).toLocaleString()}
              </Typography>
            </Alert>
          )}

          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Active Jobs
                  </Typography>
                  <Typography variant="h3" color="primary.main">
                    {status?.active_jobs || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Currently running
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    System Status
                  </Typography>
                  <Chip
                    label={status?.expired ? 'EXPIRED' : 'ACTIVE'}
                    color={status?.expired ? 'error' : 'success'}
                    sx={{ mt: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    License status
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    API Server
                  </Typography>
                  <Chip
                    label={health?.status === 'healthy' ? 'ONLINE' : 'OFFLINE'}
                    color={health?.status === 'healthy' ? 'success' : 'error'}
                    sx={{ mt: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    Connection status
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    API Port
                  </Typography>
                  <Typography variant="h4" fontFamily="monospace">
                    8000
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    localhost
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  startIcon={<PlayArrow />}
                  onClick={() => router.push('/generate')}
                  sx={{ py: 2 }}
                >
                  Create New Job
                </Button>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Button
                  fullWidth
                  variant="outlined"
                  size="large"
                  startIcon={<History />}
                  onClick={() => router.push('/history')}
                  sx={{ py: 2 }}
                >
                  View History
                </Button>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Button
                  fullWidth
                  variant="outlined"
                  size="large"
                  startIcon={<Settings />}
                  onClick={() => router.push('/settings')}
                  sx={{ py: 2 }}
                >
                  Settings
                </Button>
              </Grid>
            </Grid>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Getting Started
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="body1" sx={{ mb: 2 }}>
              Welcome to the Facebook Account Checker. This application allows you to verify phone numbers on Facebook.
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              <strong>Step 1:</strong> Configure proxy settings in the Settings page (optional)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              <strong>Step 2:</strong> Go to Generate page and enter phone numbers to check
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              <strong>Step 3:</strong> Monitor progress in real-time and view results
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>Step 4:</strong> Access completed jobs and export results from the History page
            </Typography>
          </Paper>
        </>
      )}
    </Box>
  );
}
