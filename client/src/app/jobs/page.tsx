"use client";
import React, {useState, useEffect} from "react";
import {HiPlay, HiStop, HiTrash, HiEye, HiArrowPath, HiDocumentText} from "react-icons/hi2";
import {toast} from "react-toastify";
import SimpleBar from "simplebar-react";
import "simplebar-react/dist/simplebar.min.css";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import IconButton from "@mui/material/IconButton";
import LinearProgress from "@mui/material/LinearProgress";
import Tooltip from "@mui/material/Tooltip";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import {getAllJobs, stopJob, deleteJob, getJobDetails, getJobLogs} from "@/services/api";
import {Job, JobStatus, LogEntry} from "@/types/api";
import {useRouter} from "next/navigation";

export default function JobsPage() {
    const router = useRouter();
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [jobLogs, setJobLogs] = useState<LogEntry[]>([]);
    const [logsDialogOpen, setLogsDialogOpen] = useState(false);

    // Load jobs on mount and refresh periodically
    useEffect(() => {
        loadJobs();
        const interval = setInterval(loadJobs, 3000); // Refresh every 3 seconds
        return () => clearInterval(interval);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const loadJobs = async () => {
        try {
            const response = await getAllJobs();
            if (response.success && response.data) {
                setJobs(response.data);
            } else {
                if (loading) {
                    toast.error(response.error || "Failed to load jobs");
                }
            }
        } catch (error) {
            console.error("Error loading jobs:", error);
            if (loading) {
                toast.error("Failed to connect to API");
            }
        } finally {
            setLoading(false);
        }
    };

    const handleStopJob = async (jobId: string, event: React.MouseEvent) => {
        event.stopPropagation();
        try {
            const response = await stopJob(jobId);
            if (response.success) {
                toast.success("Job stopped successfully");
                loadJobs();
            } else {
                toast.error(response.error || "Failed to stop job");
            }
        } catch (error) {
            console.error("Error stopping job:", error);
            toast.error("Failed to stop job");
        }
    };

    const handleDeleteJob = async (jobId: string, event: React.MouseEvent) => {
        event.stopPropagation();
        if (!window.confirm("Are you sure you want to delete this job?")) {
            return;
        }
        try {
            const response = await deleteJob(jobId);
            if (response.success) {
                toast.success("Job deleted successfully");
                loadJobs();
            } else {
                toast.error(response.error || "Failed to delete job");
            }
        } catch (error) {
            console.error("Error deleting job:", error);
            toast.error("Failed to delete job");
        }
    };

    const handleViewLogs = async (job: Job, event: React.MouseEvent) => {
        event.stopPropagation();
        setSelectedJob(job);
        try {
            const response = await getJobLogs(job.job_id);
            if (response.success && response.data) {
                setJobLogs(response.data.logs);
                setLogsDialogOpen(true);
            } else {
                toast.error(response.error || "Failed to load logs");
            }
        } catch (error) {
            console.error("Error loading logs:", error);
            toast.error("Failed to load logs");
        }
    };

    const handleViewDetails = async (jobId: string) => {
        try {
            const response = await getJobDetails(jobId);
            if (response.success && response.data) {
                const job = response.data;
                if (job.status === "completed") {
                    router.push(`/history?job=${jobId}`);
                } else {
                    toast.info(`Job is ${job.status}. Progress: ${job.processed}/${job.total_phones}`);
                }
            }
        } catch (error) {
            console.error("Error loading job details:", error);
        }
    };

    const getStatusColor = (status: JobStatus): "default" | "primary" | "success" | "error" | "warning" => {
        switch (status) {
            case "running":
                return "primary";
            case "completed":
                return "success";
            case "error":
                return "error";
            case "stopped":
                return "warning";
            default:
                return "default";
        }
    };

    const calculateProgress = (job: Job): number => {
        if (job.total_phones === 0) return 0;
        return (job.processed / job.total_phones) * 100;
    };

    if (loading) {
        return (
            <Box sx={{height: "100%", display: "flex", alignItems: "center", justifyContent: "center"}}>
                <Typography variant="body1" sx={{color: "text.secondary"}}>
                    Loading jobs...
                </Typography>
            </Box>
        );
    }

    return (
        <Box sx={{height: "100%", display: "flex", flexDirection: "column", overflow: "hidden"}}>
            {/* Header */}
            <Box sx={{px: 6, pt: 5, pb: 3, display: "flex", alignItems: "center", justifyContent: "space-between"}}>
                <Box>
                    <Typography variant="h4" sx={{fontWeight: 700, mb: 1, letterSpacing: "-0.02em"}}>
                        Jobs Management
                    </Typography>
                    <Typography variant="body2" sx={{color: "text.secondary"}}>
                        Monitor and manage all checking jobs
                    </Typography>
                </Box>
                <Box sx={{display: "flex", gap: 2}}>
                    <Button variant="outlined" startIcon={<HiArrowPath size={16} />} onClick={loadJobs}>
                        Refresh
                    </Button>
                    <Button variant="contained" startIcon={<HiPlay size={16} />} onClick={() => router.push("/generate")}>
                        New Job
                    </Button>
                </Box>
            </Box>

            {/* Stats Bar */}
            <Box sx={{px: 6, pb: 3}}>
                <Box
                    sx={{
                        display: "flex",
                        gap: 3,
                        p: 2.5,
                        bgcolor: "background.paper",
                        borderRadius: 2,
                        border: "1px solid",
                        borderColor: "divider",
                    }}
                >
                    <Box sx={{display: "flex", alignItems: "center", gap: 1.5}}>
                        <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                            Total Jobs:
                        </Typography>
                        <Typography variant="body1" sx={{fontWeight: 600}}>
                            {jobs.length}
                        </Typography>
                    </Box>
                    <Box sx={{display: "flex", alignItems: "center", gap: 1.5}}>
                        <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                            Running:
                        </Typography>
                        <Typography variant="body1" sx={{fontWeight: 600, color: "primary.main"}}>
                            {jobs.filter((j) => j.status === "running").length}
                        </Typography>
                    </Box>
                    <Box sx={{display: "flex", alignItems: "center", gap: 1.5}}>
                        <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                            Completed:
                        </Typography>
                        <Typography variant="body1" sx={{fontWeight: 600, color: "success.main"}}>
                            {jobs.filter((j) => j.status === "completed").length}
                        </Typography>
                    </Box>
                    <Box sx={{display: "flex", alignItems: "center", gap: 1.5}}>
                        <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                            Failed:
                        </Typography>
                        <Typography variant="body1" sx={{fontWeight: 600, color: "error.main"}}>
                            {jobs.filter((j) => j.status === "error").length}
                        </Typography>
                    </Box>
                </Box>
            </Box>

            {/* Jobs List */}
            <Box sx={{px: 6, pb: 6, flexGrow: 1, overflow: "hidden"}}>
                <SimpleBar style={{maxHeight: "100%", height: "100%"}}>
                    {jobs.length === 0 ? (
                        <Box
                            sx={{
                                height: "100%",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                minHeight: 300,
                            }}
                        >
                            <Box sx={{textAlign: "center"}}>
                                <Box
                                    sx={{
                                        width: 64,
                                        height: 64,
                                        borderRadius: 2,
                                        bgcolor: "rgba(99, 102, 241, 0.1)",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        mx: "auto",
                                        mb: 2,
                                    }}
                                >
                                    <HiPlay size={32} style={{opacity: 0.4}} />
                                </Box>
                                <Typography variant="body1" sx={{fontWeight: 600, mb: 1}}>
                                    No jobs yet
                                </Typography>
                                <Typography variant="body2" sx={{color: "text.secondary", mb: 3}}>
                                    Create your first job to start checking phone numbers
                                </Typography>
                                <Button variant="contained" startIcon={<HiPlay size={16} />} onClick={() => router.push("/generate")}>
                                    Create Job
                                </Button>
                            </Box>
                        </Box>
                    ) : (
                        <Box sx={{display: "flex", flexDirection: "column", gap: 2}}>
                            {jobs.map((job) => (
                                <Card
                                    key={job.job_id}
                                    sx={{
                                        cursor: "pointer",
                                        transition: "all 0.2s ease",
                                        "&:hover": {
                                            boxShadow: 3,
                                        },
                                    }}
                                    onClick={() => handleViewDetails(job.job_id)}
                                >
                                    <CardContent sx={{p: 3}}>
                                        <Box sx={{display: "flex", alignItems: "flex-start", justifyContent: "space-between", mb: 2}}>
                                            <Box sx={{flex: 1}}>
                                                <Box sx={{display: "flex", alignItems: "center", gap: 2, mb: 1}}>
                                                    <Typography variant="h6" sx={{fontWeight: 600, fontSize: "1rem"}}>
                                                        Job #{job.job_id.substring(0, 8)}
                                                    </Typography>
                                                    <Chip label={job.status} size="small" color={getStatusColor(job.status)} />
                                                </Box>
                                                <Box sx={{display: "flex", gap: 3, mb: 2}}>
                                                    <Typography variant="caption" sx={{color: "text.secondary"}}>
                                                        Created: {new Date(job.created_at).toLocaleString()}
                                                    </Typography>
                                                    {job.completed_at && (
                                                        <Typography variant="caption" sx={{color: "text.secondary"}}>
                                                            Completed: {new Date(job.completed_at).toLocaleString()}
                                                        </Typography>
                                                    )}
                                                </Box>
                                                <Box sx={{display: "flex", gap: 4}}>
                                                    <Box>
                                                        <Typography variant="caption" sx={{color: "text.secondary", display: "block"}}>
                                                            Total
                                                        </Typography>
                                                        <Typography variant="body2" sx={{fontWeight: 600}}>
                                                            {job.total_phones}
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" sx={{color: "text.secondary", display: "block"}}>
                                                            Processed
                                                        </Typography>
                                                        <Typography variant="body2" sx={{fontWeight: 600}}>
                                                            {job.processed}
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" sx={{color: "text.secondary", display: "block"}}>
                                                            Success
                                                        </Typography>
                                                        <Typography variant="body2" sx={{fontWeight: 600, color: "success.main"}}>
                                                            {job.successful}
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" sx={{color: "text.secondary", display: "block"}}>
                                                            Failed
                                                        </Typography>
                                                        <Typography variant="body2" sx={{fontWeight: 600, color: "error.main"}}>
                                                            {job.failed}
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" sx={{color: "text.secondary", display: "block"}}>
                                                            Workers
                                                        </Typography>
                                                        <Typography variant="body2" sx={{fontWeight: 600}}>
                                                            {job.workers}
                                                        </Typography>
                                                    </Box>
                                                </Box>
                                            </Box>
                                            <Box sx={{display: "flex", gap: 1}}>
                                                <Tooltip title="View Logs">
                                                    <IconButton size="small" onClick={(e) => handleViewLogs(job, e)}>
                                                        <HiDocumentText size={18} />
                                                    </IconButton>
                                                </Tooltip>
                                                <Tooltip title="View Details">
                                                    <IconButton
                                                        size="small"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleViewDetails(job.job_id);
                                                        }}
                                                    >
                                                        <HiEye size={18} />
                                                    </IconButton>
                                                </Tooltip>
                                                {job.status === "running" && (
                                                    <Tooltip title="Stop Job">
                                                        <IconButton
                                                            size="small"
                                                            color="error"
                                                            onClick={(e) => handleStopJob(job.job_id, e)}
                                                        >
                                                            <HiStop size={18} />
                                                        </IconButton>
                                                    </Tooltip>
                                                )}
                                                {(job.status === "completed" || job.status === "stopped" || job.status === "error") && (
                                                    <Tooltip title="Delete Job">
                                                        <IconButton
                                                            size="small"
                                                            color="error"
                                                            onClick={(e) => handleDeleteJob(job.job_id, e)}
                                                        >
                                                            <HiTrash size={18} />
                                                        </IconButton>
                                                    </Tooltip>
                                                )}
                                            </Box>
                                        </Box>
                                        {job.status === "running" && (
                                            <Box>
                                                <LinearProgress variant="determinate" value={calculateProgress(job)} sx={{mb: 1}} />
                                                <Typography variant="caption" sx={{color: "text.secondary"}}>
                                                    Progress: {calculateProgress(job).toFixed(1)}%
                                                </Typography>
                                            </Box>
                                        )}
                                        {job.error && (
                                            <Box sx={{mt: 2, p: 1.5, bgcolor: "error.main", borderRadius: 1, opacity: 0.1}}>
                                                <Typography variant="caption" sx={{color: "error.main"}}>
                                                    Error: {job.error}
                                                </Typography>
                                            </Box>
                                        )}
                                    </CardContent>
                                </Card>
                            ))}
                        </Box>
                    )}
                </SimpleBar>
            </Box>

            {/* Logs Dialog */}
            <Dialog open={logsDialogOpen} onClose={() => setLogsDialogOpen(false)} maxWidth="md" fullWidth>
                <DialogTitle>Job Logs - {selectedJob?.job_id.substring(0, 8)}</DialogTitle>
                <DialogContent dividers>
                    <SimpleBar style={{maxHeight: "400px"}}>
                        {jobLogs.length === 0 ? (
                            <Typography variant="body2" sx={{color: "text.secondary", textAlign: "center", py: 4}}>
                                No logs available
                            </Typography>
                        ) : (
                            <Box sx={{fontFamily: "monospace", fontSize: "0.875rem"}}>
                                {jobLogs.map((log, index) => (
                                    <Box key={index} sx={{mb: 1, pb: 1, borderBottom: "1px solid", borderColor: "divider"}}>
                                        <Box sx={{display: "flex", gap: 2}}>
                                            <Typography variant="caption" sx={{color: "text.secondary", minWidth: 180}}>
                                                {log.timestamp}
                                            </Typography>
                                            <Chip
                                                label={log.level}
                                                size="small"
                                                color={log.level === "ERROR" ? "error" : log.level === "WARNING" ? "warning" : "default"}
                                                sx={{height: 20}}
                                            />
                                            <Typography variant="body2">{log.message}</Typography>
                                        </Box>
                                    </Box>
                                ))}
                            </Box>
                        )}
                    </SimpleBar>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setLogsDialogOpen(false)}>Close</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}
