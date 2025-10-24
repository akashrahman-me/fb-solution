"use client";
import { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  LinearProgress,
  Alert,
  Chip,
  Stack,
  Switch,
  FormControlLabel,
  Card,
  CardContent,
  Grid,
  Divider,
} from '@mui/material';
import { PlayArrow, Stop, CheckCircle, Cancel, Error } from '@mui/icons-material';
import { toast } from 'react-toastify';
import { apiService } from '@/services/api';
import { Job, JobResult, StreamUpdate } from '@/types/api';

export default function GeneratePage() {
  const [phoneNumbers, setPhoneNumbers] = useState('');
  const [workers, setWorkers] = useState(5);
  const [headless, setHeadless] = useState(true);
  const [loading, setLoading] = useState(false);
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [streamUpdate, setStreamUpdate] = useState<StreamUpdate | null>(null);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  const handleStartJob = async () => {
    const numbers = phoneNumbers
      .split('\n')
      .map(n => n.trim())
      .filter(n => n.length > 0);

    if (numbers.length === 0) {
      toast.error('Please enter at least one phone number');
      return;
    }

    if (workers < 1 || workers > 20) {
      toast.error('Workers must be between 1 and 20');
      return;
    }

    try {
      setLoading(true);
      const job = await apiService.createJob({
        phone_numbers: numbers,
        workers,
        headless,
      });

      setCurrentJob(job);
      toast.success(`Job created: ${job.job_id}`);

      // Start streaming updates
      const es = apiService.streamJobProgress(job.job_id);
      es.onmessage = (event) => {
        const update: StreamUpdate = JSON.parse(event.data);
        setStreamUpdate(update);
        
        // Update job status
        if (update.status === 'completed' || update.status === 'stopped' || update.status === 'error') {
          es.close();
          setEventSource(null);
          // Fetch final job details
          apiService.getJob(job.job_id).then(setCurrentJob);
        }
      };

      es.onerror = () => {
        es.close();
        setEventSource(null);
      };

      setEventSource(es);
    } catch (error: any) {
      toast.error(error.message || 'Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  const handleStopJob = async () => {
    if (!currentJob) return;

    try {
      await apiService.stopJob(currentJob.job_id);
      toast.info('Job stopped');
      if (eventSource) {
        eventSource.close();
        setEventSource(null);
      }
      const updatedJob = await apiService.getJob(currentJob.job_id);
      setCurrentJob(updatedJob);
    } catch (error: any) {
      toast.error(error.message || 'Failed to stop job');
    }
  };

  const handleReset = () => {
    if (eventSource) {
      eventSource.close();
    }
    setCurrentJob(null);
    setStreamUpdate(null);
    setEventSource(null);
    setPhoneNumbers('');
  };

  const isRunning = currentJob?.status === 'running' || currentJob?.status === 'pending';
  const progress = streamUpdate ? (streamUpdate.processed / streamUpdate.total) * 100 : 0;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Generate Check Job
      </Typography>

      {!currentJob && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Job Configuration
          </Typography>
          
          <TextField
            fullWidth
            multiline
            rows={10}
            label="Phone Numbers"
            placeholder="Enter phone numbers (one per line)&#10;1234567890&#10;0987654321"
            value={phoneNumbers}
            onChange={(e) => setPhoneNumbers(e.target.value)}
            sx={{ mb: 2 }}
          />

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Workers"
                value={workers}
                onChange={(e) => setWorkers(parseInt(e.target.value) || 1)}
                inputProps={{ min: 1, max: 20 }}
                helperText="Number of concurrent workers (1-20)"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={headless}
                    onChange={(e) => setHeadless(e.target.checked)}
                  />
                }
                label="Headless Mode (Run browsers in background)"
              />
            </Grid>
          </Grid>

          <Button
            variant="contained"
            size="large"
            startIcon={<PlayArrow />}
            onClick={handleStartJob}
            disabled={loading}
            fullWidth
          >
            Start Job
          </Button>
        </Paper>
      )}

      {currentJob && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Job: {currentJob.job_id}
            </Typography>
            <Chip
              label={currentJob.status.toUpperCase()}
              color={
                currentJob.status === 'completed' ? 'success' :
                currentJob.status === 'running' ? 'primary' :
                currentJob.status === 'error' ? 'error' : 'default'
              }
            />
          </Box>

          {isRunning && (
            <Box sx={{ mb: 3 }}>
              <LinearProgress variant="determinate" value={progress} sx={{ mb: 1 }} />
              <Typography variant="body2" color="text.secondary">
                {streamUpdate ? `${streamUpdate.processed} / ${streamUpdate.total}` : 'Starting...'}
              </Typography>
            </Box>
          )}

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>Total</Typography>
                  <Typography variant="h4">{streamUpdate?.total || currentJob.total}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>Found</Typography>
                  <Typography variant="h4" color="success.main">{streamUpdate?.found || currentJob.found}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>Not Found</Typography>
                  <Typography variant="h4" color="warning.main">{streamUpdate?.not_found || currentJob.not_found}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>Errors</Typography>
                  <Typography variant="h4" color="error.main">{streamUpdate?.errors || currentJob.errors}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {streamUpdate?.latest_result && (
            <Alert severity={streamUpdate.latest_result.exists ? 'success' : 'info'} sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>{streamUpdate.latest_result.phone_number}</strong>: {
                  streamUpdate.latest_result.exists
                    ? `Found - ${streamUpdate.latest_result.profile_name}`
                    : streamUpdate.latest_result.error || 'Not found'
                }
              </Typography>
            </Alert>
          )}

          <Stack direction="row" spacing={2}>
            {isRunning ? (
              <Button
                variant="contained"
                color="error"
                startIcon={<Stop />}
                onClick={handleStopJob}
                fullWidth
              >
                Stop Job
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleReset}
                fullWidth
              >
                New Job
              </Button>
            )}
          </Stack>

          {currentJob.results.length > 0 && (
            <>
              <Divider sx={{ my: 3 }} />
              <Typography variant="h6" gutterBottom>
                Results
              </Typography>
              <Stack spacing={1}>
                {currentJob.results.map((result, index) => (
                  <Paper key={index} sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      {result.exists ? (
                        <CheckCircle color="success" />
                      ) : result.error ? (
                        <Error color="error" />
                      ) : (
                        <Cancel color="warning" />
                      )}
                      <Box>
                        <Typography variant="body1" fontWeight="bold">
                          {result.phone_number}
                        </Typography>
                        {result.exists && result.profile_name && (
                          <Typography variant="body2" color="text.secondary">
                            {result.profile_name}
                          </Typography>
                        )}
                        {result.error && (
                          <Typography variant="body2" color="error">
                            {result.error}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                    {result.exists && result.profile_url && (
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => window.open(result.profile_url, '_blank')}
                      >
                        View Profile
                      </Button>
                    )}
                  </Paper>
                ))}
              </Stack>
            </>
          )}
        </Paper>
      )}
    </Box>
  );
}

