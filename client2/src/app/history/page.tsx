"use client";
import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Refresh, Delete, Visibility, CheckCircle, Cancel, Error as ErrorIcon } from '@mui/icons-material';
import { toast } from 'react-toastify';
import { apiService } from '@/services/api';
import { Job, JobResult } from '@/types/api';

export default function HistoryPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const data = await apiService.listJobs();
      setJobs(data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
    } catch (error: any) {
      toast.error(error.message || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const handleViewDetails = async (jobId: string) => {
    try {
      const job = await apiService.getJob(jobId);
      setSelectedJob(job);
      setDetailsOpen(true);
    } catch (error: any) {
      toast.error(error.message || 'Failed to load job details');
    }
  };

  const handleDelete = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
      await apiService.deleteJob(jobId);
      toast.success('Job deleted');
      loadJobs();
    } catch (error: any) {
      toast.error(error.message || 'Failed to delete job');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'primary';
      case 'error': return 'error';
      case 'stopped': return 'warning';
      default: return 'default';
    }
  };

  const exportResults = (job: Job) => {
    const csv = [
      ['Phone Number', 'Status', 'Profile Name', 'Profile URL', 'Error'].join(','),
      ...job.results.map(r => [
        r.phone_number,
        r.exists ? 'Found' : 'Not Found',
        r.profile_name || '',
        r.profile_url || '',
        r.error || ''
      ].map(field => `"${field}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `job_${job.job_id}_results.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Job History</Typography>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={loadJobs}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : jobs.length === 0 ? (
        <Alert severity="info">No jobs found. Create a job from the Generate page.</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Job ID</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Total</TableCell>
                <TableCell align="right">Found</TableCell>
                <TableCell align="right">Not Found</TableCell>
                <TableCell align="right">Errors</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {jobs.map((job) => (
                <TableRow key={job.job_id} hover>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {job.job_id.substring(0, 8)}...
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={job.status.toUpperCase()}
                      color={getStatusColor(job.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">{job.total}</TableCell>
                  <TableCell align="right">
                    <Typography color="success.main">{job.found}</Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography color="warning.main">{job.not_found}</Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography color="error.main">{job.errors}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{formatDate(job.created_at)}</Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Stack direction="row" spacing={1} justifyContent="center">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleViewDetails(job.job_id)}
                      >
                        <Visibility />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(job.job_id)}
                      >
                        <Delete />
                      </IconButton>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Job Details: {selectedJob?.job_id.substring(0, 8)}...
        </DialogTitle>
        <DialogContent>
          {selectedJob && (
            <Box>
              <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                <Chip label={`Status: ${selectedJob.status.toUpperCase()}`} color={getStatusColor(selectedJob.status) as any} />
                <Chip label={`Workers: ${selectedJob.workers}`} />
                <Chip label={selectedJob.headless ? 'Headless' : 'Visible'} />
              </Stack>

              <Typography variant="body2" gutterBottom>
                Created: {formatDate(selectedJob.created_at)}
              </Typography>
              {selectedJob.completed_at && (
                <Typography variant="body2" gutterBottom>
                  Completed: {formatDate(selectedJob.completed_at)}
                </Typography>
              )}

              <Box sx={{ my: 3 }}>
                <Typography variant="h6" gutterBottom>Summary</Typography>
                <Stack direction="row" spacing={2}>
                  <Paper sx={{ p: 2, flex: 1 }}>
                    <Typography color="text.secondary">Total</Typography>
                    <Typography variant="h5">{selectedJob.total}</Typography>
                  </Paper>
                  <Paper sx={{ p: 2, flex: 1 }}>
                    <Typography color="text.secondary">Found</Typography>
                    <Typography variant="h5" color="success.main">{selectedJob.found}</Typography>
                  </Paper>
                  <Paper sx={{ p: 2, flex: 1 }}>
                    <Typography color="text.secondary">Not Found</Typography>
                    <Typography variant="h5" color="warning.main">{selectedJob.not_found}</Typography>
                  </Paper>
                  <Paper sx={{ p: 2, flex: 1 }}>
                    <Typography color="text.secondary">Errors</Typography>
                    <Typography variant="h5" color="error.main">{selectedJob.errors}</Typography>
                  </Paper>
                </Stack>
              </Box>

              {selectedJob.results.length > 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>Results</Typography>
                  <Stack spacing={1} sx={{ maxHeight: 400, overflow: 'auto' }}>
                    {selectedJob.results.map((result, index) => (
                      <Paper key={index} sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          {result.exists ? (
                            <CheckCircle color="success" />
                          ) : result.error ? (
                            <ErrorIcon color="error" />
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
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          {selectedJob && selectedJob.results.length > 0 && (
            <Button onClick={() => exportResults(selectedJob)}>
              Export CSV
            </Button>
          )}
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

