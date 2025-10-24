import {useState, useRef, useEffect} from "react";
import {toast} from "react-toastify";
import {createJob, stopJob, streamJobProgress, pollJobStatus, getJobResults, getJobLogs} from "@/services/api";
import {ProxyConfig} from "@/types/api";

interface ResultItem {
    phone: string;
    status: "success" | "failed";
    message: string;
}

interface JobProgress {
    processed: number;
    total: number;
    percentage: number;
}

export function useJobManager() {
    const [results, setResults] = useState<ResultItem[]>([]);
    const [logs, setLogs] = useState<string[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const [currentJobId, setCurrentJobId] = useState<string | null>(null);
    const [progress, setProgress] = useState<JobProgress>({processed: 0, total: 0, percentage: 0});

    const eventSourceRef = useRef<EventSource | null>(null);
    const logsFetchIntervalRef = useRef<NodeJS.Timeout | null>(null);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
            if (logsFetchIntervalRef.current) {
                clearInterval(logsFetchIntervalRef.current);
            }
        };
    }, []);

    // Fetch logs periodically while job is running
    useEffect(() => {
        if (isRunning && currentJobId) {
            fetchLogs(currentJobId);
            logsFetchIntervalRef.current = setInterval(() => {
                fetchLogs(currentJobId);
            }, 2000);
        } else {
            if (logsFetchIntervalRef.current) {
                clearInterval(logsFetchIntervalRef.current);
                logsFetchIntervalRef.current = null;
            }
        }

        return () => {
            if (logsFetchIntervalRef.current) {
                clearInterval(logsFetchIntervalRef.current);
            }
        };
    }, [isRunning, currentJobId]);

    const fetchLogs = async (jobId: string) => {
        try {
            const response = await getJobLogs(jobId);
            if (response.success && response.data) {
                setLogs(response.data.logs);
            }
        } catch (error) {
            console.error("Error fetching logs:", error);
        }
    };

    const handleJobComplete = async (jobId: string) => {
        try {
            const [resultsRes, logsRes] = await Promise.all([getJobResults(jobId), getJobLogs(jobId)]);

            if (resultsRes.success && resultsRes.data) {
                setResults(resultsRes.data.results);
                toast.success(`Job completed! Processed ${resultsRes.data.results.length} numbers`);
            }

            if (logsRes.success && logsRes.data) {
                setLogs(logsRes.data.logs);
            }
        } catch (error) {
            console.error("Error fetching final results:", error);
        } finally {
            setIsRunning(false);
            setCurrentJobId(null);
        }
    };

    const handleFallbackPolling = async (jobId: string, total: number) => {
        try {
            await pollJobStatus(
                jobId,
                (status) => {
                    setProgress({
                        processed: status.processed_count,
                        total: total,
                        percentage: (status.processed_count / total) * 100,
                    });
                },
                2000
            );
            handleJobComplete(jobId);
        } catch (error) {
            console.error("Polling error:", error);
            toast.error("Failed to track job progress");
            setIsRunning(false);
        }
    };

    const startJob = async (phones: string[], concurrency: number, headless: boolean, proxy?: ProxyConfig, licenseKey?: string) => {
        if (phones.length === 0) {
            toast.error("Please enter at least one phone number");
            return;
        }

        setIsRunning(true);
        setResults([]);
        setLogs([]);
        setProgress({processed: 0, total: phones.length, percentage: 0});
        toast.info("Creating job...");

        try {
            const response = await createJob({
                phone_numbers: phones,
                workers: concurrency,
                headless: headless,
                proxy: proxy,
                license_key: licenseKey,
            });

            if (!response.success || !response.data) {
                throw new Error(response.error || "Failed to create job");
            }

            const jobId = response.data.job_id;
            setCurrentJobId(jobId);
            toast.success("Job created! Processing...");

            eventSourceRef.current = streamJobProgress(
                jobId,
                (event) => {
                    if (event.status === "running" || event.status === "completed") {
                        setProgress({
                            processed: event.processed_count || 0,
                            total: event.total_numbers || phones.length,
                            percentage: event.total_numbers ? ((event.processed_count || 0) / event.total_numbers) * 100 : 0,
                        });
                    }
                    if (event.status === "completed") {
                        handleJobComplete(jobId);
                    }
                },
                (error) => {
                    console.warn("SSE stream error, falling back to polling:", error);
                    toast.info("Using polling mode for progress updates");
                    handleFallbackPolling(jobId, phones.length);
                },
                () => {
                    console.log("Stream closed");
                }
            );
        } catch (error) {
            console.error("Error starting job:", error);
            toast.error(error instanceof Error ? error.message : "Failed to start job");
            setIsRunning(false);
        }
    };

    const stopCurrentJob = async () => {
        if (!currentJobId) {
            setIsRunning(false);
            return;
        }

        try {
            toast.info("Stopping job...");
            const response = await stopJob(currentJobId);

            if (response.success) {
                toast.warning("Job stopped");
                if (eventSourceRef.current) {
                    eventSourceRef.current.close();
                }
                setIsRunning(false);
                setCurrentJobId(null);
            } else {
                toast.error(response.error || "Failed to stop job");
            }
        } catch (error) {
            console.error("Error stopping job:", error);
            toast.error("Failed to stop job");
        }
    };

    const clearResults = () => {
        setResults([]);
        setLogs([]);
    };

    return {
        results,
        logs,
        isRunning,
        progress,
        startJob,
        stopCurrentJob,
        clearResults,
    };
}
