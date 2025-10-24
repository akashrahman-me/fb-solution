"use client";
import React, {useState, useMemo, useEffect} from "react";
import {HiMagnifyingGlass, HiTrash, HiClipboardDocument, HiCheck, HiFunnel, HiArrowDownTray, HiArrowPath} from "react-icons/hi2";
import {toast} from "react-toastify";
import SimpleBar from "simplebar-react";
import "simplebar-react/dist/simplebar.min.css";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import InputAdornment from "@mui/material/InputAdornment";
import IconButton from "@mui/material/IconButton";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import {getAllJobs, getJobResults} from "@/services/api";
import {PhoneResult} from "@/types/api";
import {useSearchParams} from "next/navigation";

interface HistoryItem {
    id: string;
    phone: string;
    registered: boolean;
    name?: string;
    profile_url?: string;
    status: "success" | "failed";
    timestamp: string;
    date: Date;
    jobId: string;
}

export default function HistoryPage() {
    const searchParams = useSearchParams();
    const jobIdFromUrl = searchParams.get("job");

    const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState<"all" | "registered" | "not-registered">("all");
    const [copiedId, setCopiedId] = useState<string | null>(null);

    useEffect(() => {
        loadAllResults();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [jobIdFromUrl]);

    const loadAllResults = async () => {
        setLoading(true);
        try {
            const jobsResponse = await getAllJobs();
            if (!jobsResponse.success || !jobsResponse.data) {
                toast.error("Failed to load jobs");
                setLoading(false);
                return;
            }

            const completedJobs = jobsResponse.data.filter((job) => job.status === "completed");
            const allResults: HistoryItem[] = [];

            for (const job of completedJobs) {
                // If jobId from URL is specified, only load that job
                if (jobIdFromUrl && job.job_id !== jobIdFromUrl) {
                    continue;
                }

                const resultsResponse = await getJobResults(job.job_id);
                if (resultsResponse.success && resultsResponse.data) {
                    const jobResults = resultsResponse.data.results.map((result: PhoneResult, index: number) => ({
                        id: `${job.job_id}-${index}`,
                        phone: result.phone,
                        registered: result.registered,
                        name: result.name,
                        profile_url: result.profile_url,
                        status: (result.error ? "failed" : "success") as "success" | "failed",
                        timestamp: new Date(result.timestamp).toLocaleString(),
                        date: new Date(result.timestamp),
                        jobId: job.job_id,
                    }));
                    allResults.push(...jobResults);
                }
            }

            // Sort by date, newest first
            allResults.sort((a, b) => b.date.getTime() - a.date.getTime());
            setHistoryItems(allResults);
        } catch (error) {
            console.error("Error loading results:", error);
            toast.error("Failed to load history");
        } finally {
            setLoading(false);
        }
    };

    // Filter and search logic
    const filteredItems = useMemo(() => {
        return historyItems.filter((item) => {
            const matchesSearch =
                item.phone.toLowerCase().includes(searchQuery.toLowerCase()) ||
                (item.name && item.name.toLowerCase().includes(searchQuery.toLowerCase()));
            const matchesStatus =
                statusFilter === "all" ||
                (statusFilter === "registered" && item.registered) ||
                (statusFilter === "not-registered" && !item.registered);
            return matchesSearch && matchesStatus;
        });
    }, [historyItems, searchQuery, statusFilter]);

    const handleCopyItem = (id: string, phone: string, registered: boolean, name?: string) => {
        const text = `${phone}|${registered ? "Registered" : "Not Registered"}${name ? `|${name}` : ""}`;
        navigator.clipboard.writeText(text);
        setCopiedId(id);

        setTimeout(() => {
            setCopiedId(null);
        }, 2000);
    };

    const handleDeleteItem = (id: string) => {
        setHistoryItems((prev) => prev.filter((item) => item.id !== id));
        toast.success("Item deleted from history");
    };

    const handleClearAll = () => {
        if (window.confirm("Are you sure you want to clear all history?")) {
            setHistoryItems([]);
            toast.success("All history cleared");
        }
    };

    const handleExport = () => {
        const csv = [
            "Phone,Registered,Name,Profile URL,Status,Timestamp",
            ...filteredItems.map(
                (item) =>
                    `${item.phone},${item.registered ? "Yes" : "No"},${item.name || "N/A"},${item.profile_url || "N/A"},${item.status},${
                        item.timestamp
                    }`
            ),
        ].join("\n");

        const blob = new Blob([csv], {type: "text/csv"});
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `fb-check-history-${new Date().toISOString().split("T")[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success("History exported successfully");
    };

    const stats = {
        total: historyItems.length,
        registered: historyItems.filter((i) => i.registered).length,
        notRegistered: historyItems.filter((i) => !i.registered).length,
    };

    return (
        <Box sx={{height: "100%", display: "flex", flexDirection: "column", overflow: "hidden"}}>
            <SimpleBar style={{maxHeight: "100%", height: "100%"}}>
                {/* Header - Static */}
                <Box sx={{px: 6, pt: 5, pb: 3}}>
                    <Box sx={{display: "flex", alignItems: "center", justifyContent: "space-between"}}>
                        <Box>
                            <Typography variant="h4" sx={{fontWeight: 700, mb: 1, letterSpacing: "-0.02em"}}>
                                Check History
                            </Typography>
                            <Typography variant="body2" sx={{color: "text.secondary"}}>
                                View and manage results from all completed jobs
                            </Typography>
                        </Box>
                        {!loading && (
                            <Button variant="outlined" startIcon={<HiArrowPath size={16} />} onClick={loadAllResults}>
                                Refresh
                            </Button>
                        )}
                    </Box>
                </Box>

                {loading ? (
                    <Box sx={{display: "flex", alignItems: "center", justifyContent: "center", minHeight: 400}}>
                        <Typography variant="body1" sx={{color: "text.secondary"}}>
                            Loading history...
                        </Typography>
                    </Box>
                ) : (
                    <>
                        {/* Stats Cards - Static */}
                        <Box sx={{px: 6, pb: 1}}>
                            <Box sx={{display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 2.5}}>
                                <Card>
                                    <CardContent sx={{p: 3}}>
                                        <Typography
                                            variant="caption"
                                            sx={{
                                                color: "text.secondary",
                                                fontSize: "0.75rem",
                                                fontWeight: 600,
                                                textTransform: "uppercase",
                                                letterSpacing: "0.08em",
                                            }}
                                        >
                                            Total Checked
                                        </Typography>
                                        <Typography variant="h3" sx={{mt: 1.5, fontWeight: 700, fontSize: "2.25rem"}}>
                                            {stats.total}
                                        </Typography>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardContent sx={{p: 3}}>
                                        <Typography
                                            variant="caption"
                                            sx={{
                                                color: "text.secondary",
                                                fontSize: "0.75rem",
                                                fontWeight: 600,
                                                textTransform: "uppercase",
                                                letterSpacing: "0.08em",
                                            }}
                                        >
                                            Registered
                                        </Typography>
                                        <Typography
                                            variant="h3"
                                            sx={{mt: 1.5, fontWeight: 700, fontSize: "2.25rem", color: "success.main"}}
                                        >
                                            {stats.registered}
                                        </Typography>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardContent sx={{p: 3}}>
                                        <Typography
                                            variant="caption"
                                            sx={{
                                                color: "text.secondary",
                                                fontSize: "0.75rem",
                                                fontWeight: 600,
                                                textTransform: "uppercase",
                                                letterSpacing: "0.08em",
                                            }}
                                        >
                                            Not Registered
                                        </Typography>
                                        <Typography variant="h3" sx={{mt: 1.5, fontWeight: 700, fontSize: "2.25rem", color: "error.main"}}>
                                            {stats.notRegistered}
                                        </Typography>
                                    </CardContent>
                                </Card>
                            </Box>
                        </Box>

                        {/* Search and Filter Bar - Sticky */}
                        <Box
                            sx={{
                                position: "sticky",
                                top: 0,
                                zIndex: 10,
                                bgcolor: "background.default",
                                px: 6,
                                py: 2,
                            }}
                        >
                            <Box
                                sx={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 2.5,
                                    p: 2.5,
                                    bgcolor: "background.paper",
                                    borderRadius: 2,
                                    border: "1px solid",
                                    borderColor: "divider",
                                }}
                            >
                                <Box sx={{flexGrow: 1, minWidth: 300}}>
                                    <TextField
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        placeholder="Search by phone number or OTP..."
                                        fullWidth
                                        size="small"
                                        InputProps={{
                                            startAdornment: (
                                                <InputAdornment position="start">
                                                    <HiMagnifyingGlass size={18} style={{opacity: 0.5}} />
                                                </InputAdornment>
                                            ),
                                        }}
                                    />
                                </Box>

                                <Divider orientation="vertical" flexItem sx={{opacity: 0.5}} />

                                <Box sx={{display: "flex", alignItems: "center", gap: 1.5}}>
                                    <HiFunnel size={18} style={{opacity: 0.5}} />
                                    <Select
                                        value={statusFilter}
                                        onChange={(e) => setStatusFilter(e.target.value as "all" | "registered" | "not-registered")}
                                        size="small"
                                        sx={{minWidth: 160}}
                                    >
                                        <MenuItem value="all">All Status</MenuItem>
                                        <MenuItem value="registered">Registered</MenuItem>
                                        <MenuItem value="not-registered">Not Registered</MenuItem>
                                    </Select>
                                </Box>

                                <Divider orientation="vertical" flexItem sx={{opacity: 0.5}} />

                                <Box sx={{display: "flex", gap: 1.5}}>
                                    <Button
                                        onClick={handleExport}
                                        disabled={filteredItems.length === 0}
                                        variant="outlined"
                                        startIcon={<HiArrowDownTray size={16} />}
                                    >
                                        Export
                                    </Button>
                                    <Button
                                        onClick={handleClearAll}
                                        disabled={historyItems.length === 0}
                                        variant="contained"
                                        color="error"
                                        startIcon={<HiTrash size={16} />}
                                    >
                                        Clear All
                                    </Button>
                                </Box>
                            </Box>
                        </Box>

                        <Box sx={{flexGrow: 1, px: 6, pb: 6, pt: 1}}>
                            {filteredItems.length === 0 ? (
                                <Card>
                                    <Box sx={{py: 8, display: "flex", alignItems: "center", justifyContent: "center"}}>
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
                                                <HiClipboardDocument size={32} style={{opacity: 0.4}} />
                                            </Box>
                                            <Typography variant="h6" sx={{fontWeight: 600, mb: 0.5}}>
                                                {historyItems.length === 0 ? "No history yet" : "No results found"}
                                            </Typography>
                                            <Typography variant="body2" sx={{color: "text.secondary"}}>
                                                {historyItems.length === 0
                                                    ? "Generated OTPs will appear here"
                                                    : "Try adjusting your search or filters"}
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Card>
                            ) : (
                                <Box sx={{display: "flex", flexDirection: "column", gap: 1.5}}>
                                    {filteredItems.map((item) => (
                                        <Box
                                            key={item.id}
                                            sx={{
                                                p: 2.5,
                                                bgcolor: "background.paper",
                                                borderRadius: 1.5,
                                                border: "1px solid",
                                                borderColor: "divider",
                                                transition: "all 0.2s ease",
                                                "&:hover": {
                                                    borderColor: "primary.main",
                                                    bgcolor: "rgba(99, 102, 241, 0.05)",
                                                },
                                            }}
                                        >
                                            <Box sx={{display: "flex", alignItems: "flex-start", justifyContent: "space-between"}}>
                                                <Box sx={{flexGrow: 1}}>
                                                    <Box sx={{display: "flex", alignItems: "center", gap: 1.5, mb: 2}}>
                                                        <Typography variant="body1" sx={{fontWeight: 600}}>
                                                            {item.phone}
                                                        </Typography>
                                                        <Chip
                                                            label={item.status}
                                                            size="small"
                                                            color={item.status === "success" ? "success" : "error"}
                                                            sx={{height: 20, fontSize: "0.6875rem"}}
                                                        />
                                                        <Chip
                                                            label={item.registered ? "Registered" : "Not Registered"}
                                                            size="small"
                                                            color={item.registered ? "success" : "default"}
                                                            sx={{height: 20, fontSize: "0.6875rem"}}
                                                        />
                                                    </Box>
                                                    <Box sx={{display: "flex", alignItems: "center", gap: 4}}>
                                                        {item.name && (
                                                            <Box>
                                                                <Typography
                                                                    variant="caption"
                                                                    sx={{
                                                                        color: "text.secondary",
                                                                        fontSize: "0.75rem",
                                                                        fontWeight: 500,
                                                                        display: "block",
                                                                        mb: 0.5,
                                                                    }}
                                                                >
                                                                    Name
                                                                </Typography>
                                                                <Typography variant="body2" sx={{fontWeight: 600}}>
                                                                    {item.name}
                                                                </Typography>
                                                            </Box>
                                                        )}
                                                        {item.profile_url && (
                                                            <Box>
                                                                <Typography
                                                                    variant="caption"
                                                                    sx={{
                                                                        color: "text.secondary",
                                                                        fontSize: "0.75rem",
                                                                        fontWeight: 500,
                                                                        display: "block",
                                                                        mb: 0.5,
                                                                    }}
                                                                >
                                                                    Profile URL
                                                                </Typography>
                                                                <Typography
                                                                    variant="body2"
                                                                    sx={{
                                                                        color: "primary.main",
                                                                        fontSize: "0.8125rem",
                                                                        overflow: "hidden",
                                                                        textOverflow: "ellipsis",
                                                                        whiteSpace: "nowrap",
                                                                        maxWidth: 300,
                                                                    }}
                                                                >
                                                                    {item.profile_url}
                                                                </Typography>
                                                            </Box>
                                                        )}
                                                        <Box>
                                                            <Typography
                                                                variant="caption"
                                                                sx={{
                                                                    color: "text.secondary",
                                                                    fontSize: "0.75rem",
                                                                    fontWeight: 500,
                                                                    display: "block",
                                                                    mb: 0.5,
                                                                }}
                                                            >
                                                                Checked
                                                            </Typography>
                                                            <Typography
                                                                variant="body2"
                                                                sx={{color: "text.secondary", fontSize: "0.8125rem"}}
                                                            >
                                                                {item.timestamp}
                                                            </Typography>
                                                        </Box>
                                                    </Box>
                                                </Box>
                                                <Box sx={{display: "flex", alignItems: "center", gap: 1}}>
                                                    <IconButton
                                                        onClick={() => handleCopyItem(item.id, item.phone, item.registered, item.name)}
                                                        size="small"
                                                        title="Copy"
                                                    >
                                                        {copiedId === item.id ? (
                                                            <HiCheck size={18} style={{color: "#10b981"}} />
                                                        ) : (
                                                            <HiClipboardDocument size={18} style={{opacity: 0.6}} />
                                                        )}
                                                    </IconButton>
                                                    <IconButton
                                                        onClick={() => handleDeleteItem(item.id)}
                                                        size="small"
                                                        color="error"
                                                        title="Delete"
                                                    >
                                                        <HiTrash size={18} />
                                                    </IconButton>
                                                </Box>
                                            </Box>
                                        </Box>
                                    ))}
                                </Box>
                            )}
                        </Box>
                    </>
                )}
            </SimpleBar>
        </Box>
    );
}
