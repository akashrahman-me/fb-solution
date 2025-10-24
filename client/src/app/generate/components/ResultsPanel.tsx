import React, {useState} from "react";
import {HiClipboardDocument, HiCheck} from "react-icons/hi2";
import {toast} from "react-toastify";
import SimpleBar from "simplebar-react";
import "simplebar-react/dist/simplebar.min.css";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import IconButton from "@mui/material/IconButton";
import LinearProgress from "@mui/material/LinearProgress";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import {formatResultsForClipboard, formatSingleResultForClipboard} from "../utils/phoneUtils";

interface ResultItem {
    phone: string;
    status: "success" | "failed";
    message: string;
}

interface ResultsPanelProps {
    results: ResultItem[];
    logs: string[];
    isRunning: boolean;
    progress: {
        processed: number;
        total: number;
        percentage: number;
    };
}

export default function ResultsPanel({results, logs, isRunning, progress}: ResultsPanelProps) {
    const [viewMode, setViewMode] = useState<"results" | "logs">("results");
    const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

    const handleCopyResults = () => {
        const text = formatResultsForClipboard(results);
        navigator.clipboard.writeText(text);
        toast.success(`Copied ${results.length} results to clipboard!`);
    };

    const handleCopyItem = (index: number, phone: string, status: string, message: string) => {
        const text = formatSingleResultForClipboard(phone, status, message);
        navigator.clipboard.writeText(text);
        setCopiedIndex(index);
        setTimeout(() => setCopiedIndex(null), 2000);
    };

    return (
        <Card sx={{flex: 1, display: "flex", flexDirection: "column", overflow: "hidden"}}>
            {/* Header with Tabs */}
            <Box
                sx={{
                    p: 3,
                    borderBottom: "1px solid",
                    borderColor: "divider",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                }}
            >
                <Tabs value={viewMode} onChange={(_, newValue) => setViewMode(newValue)} sx={{minHeight: 40}}>
                    <Tab label={`Results (${results.length})`} value="results" sx={{minHeight: 40, textTransform: "none"}} />
                    <Tab label={`Logs (${logs.length})`} value="logs" sx={{minHeight: 40, textTransform: "none"}} />
                </Tabs>
                {viewMode === "results" && results.length > 0 && (
                    <Button onClick={handleCopyResults} variant="outlined" size="small" startIcon={<HiClipboardDocument size={16} />}>
                        Copy All
                    </Button>
                )}
            </Box>

            {/* Progress Bar */}
            {isRunning && (
                <Box sx={{px: 3, py: 2, borderBottom: "1px solid", borderColor: "divider"}}>
                    <LinearProgress variant="determinate" value={progress.percentage} sx={{mb: 1}} />
                    <Box sx={{display: "flex", justifyContent: "space-between", alignItems: "center"}}>
                        <Typography variant="caption" sx={{color: "text.secondary"}}>
                            Progress: {progress.processed} / {progress.total}
                        </Typography>
                        <Typography variant="caption" sx={{color: "primary.main", fontWeight: 600}}>
                            {progress.percentage.toFixed(1)}%
                        </Typography>
                    </Box>
                </Box>
            )}

            {/* Content Area */}
            <Box sx={{flexGrow: 1, p: 3, overflow: "hidden"}}>
                <SimpleBar style={{maxHeight: "100%", height: "100%"}}>
                    {viewMode === "results" ? (
                        <ResultsView results={results} isRunning={isRunning} copiedIndex={copiedIndex} onCopyItem={handleCopyItem} />
                    ) : (
                        <LogsView logs={logs} isRunning={isRunning} />
                    )}
                </SimpleBar>
            </Box>
        </Card>
    );
}

// Results View Sub-component
function ResultsView({
    results,
    isRunning,
    copiedIndex,
    onCopyItem,
}: {
    results: ResultItem[];
    isRunning: boolean;
    copiedIndex: number | null;
    onCopyItem: (index: number, phone: string, status: string, message: string) => void;
}) {
    if (results.length === 0) {
        return (
            <Box sx={{height: "100%", display: "flex", alignItems: "center", justifyContent: "center"}}>
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
                    <Typography variant="body2" sx={{color: "text.secondary"}}>
                        {isRunning ? "Checking numbers..." : "Results will appear here"}
                    </Typography>
                </Box>
            </Box>
        );
    }

    return (
        <Box sx={{display: "flex", flexDirection: "column", gap: 1.5}}>
            {results.map((result, index) => (
                <Box
                    key={index}
                    onClick={() => onCopyItem(index, result.phone, result.status, result.message)}
                    sx={{
                        p: 2,
                        bgcolor: "background.default",
                        borderRadius: 1.5,
                        border: "1px solid",
                        borderColor: copiedIndex === index ? "primary.main" : "divider",
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                        "&:hover": {
                            borderColor: "primary.main",
                            bgcolor: "rgba(99, 102, 241, 0.05)",
                        },
                    }}
                >
                    <Box sx={{display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1}}>
                        <Typography
                            variant="body2"
                            sx={{
                                color: "text.secondary",
                                fontSize: "0.8125rem",
                                fontFamily: "monospace",
                            }}
                        >
                            {result.phone}
                        </Typography>
                        <Box sx={{display: "flex", alignItems: "center", gap: 1}}>
                            <Chip
                                label={result.status}
                                size="small"
                                color={result.status === "success" ? "success" : "error"}
                                sx={{height: 20, fontSize: "0.6875rem"}}
                            />
                            <IconButton size="small" sx={{width: 24, height: 24}}>
                                {copiedIndex === index ? (
                                    <HiCheck size={14} style={{color: "#10b981"}} />
                                ) : (
                                    <HiClipboardDocument size={14} style={{opacity: 0.5}} />
                                )}
                            </IconButton>
                        </Box>
                    </Box>
                    <Typography variant="body2" sx={{color: "text.primary", fontSize: "0.875rem"}}>
                        {result.message}
                    </Typography>
                </Box>
            ))}
        </Box>
    );
}

// Logs View Sub-component
function LogsView({logs, isRunning}: {logs: string[]; isRunning: boolean}) {
    if (logs.length === 0) {
        return (
            <Box sx={{height: "100%", display: "flex", alignItems: "center", justifyContent: "center"}}>
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
                    <Typography variant="body2" sx={{color: "text.secondary"}}>
                        {isRunning ? "Logs will appear here..." : "No logs yet"}
                    </Typography>
                </Box>
            </Box>
        );
    }

    return (
        <Box sx={{display: "flex", flexDirection: "column", gap: 0.5, fontFamily: "monospace", fontSize: "0.8125rem"}}>
            {logs.map((log, index) => (
                <Box
                    key={index}
                    sx={{
                        p: 1,
                        bgcolor: "background.default",
                        borderRadius: 0.5,
                        color: "text.secondary",
                        fontSize: "0.75rem",
                        fontFamily: "monospace",
                        whiteSpace: "pre-wrap",
                        wordBreak: "break-word",
                    }}
                >
                    {log}
                </Box>
            ))}
        </Box>
    );
}
