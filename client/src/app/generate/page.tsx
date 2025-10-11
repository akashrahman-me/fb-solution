"use client";
import React, {useState} from "react";
import {HiPlay, HiStop, HiArrowPath, HiClipboardDocument, HiCheck, HiSparkles, HiXMark} from "react-icons/hi2";
import {toast} from "react-toastify";
import SimpleBar from "simplebar-react";
import "simplebar-react/dist/simplebar.min.css";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import IconButton from "@mui/material/IconButton";
import Divider from "@mui/material/Divider";
import Tooltip from "@mui/material/Tooltip";

export default function GeneratePage() {
    const [phoneNumbers, setPhoneNumbers] = useState("");
    const [concurrency, setConcurrency] = useState(5);
    const [results, setResults] = useState<{phone: string; otp: string; status: string}[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

    const handleStart = () => {
        setIsRunning(true);
        toast.info("Starting OTP generation...");

        // TODO: Implement OTP generation logic
        console.log("Starting OTP generation...");
        console.log(
            "Phone numbers:",
            phoneNumbers.split("\n").filter((n) => n.trim())
        );
        console.log("Concurrency:", concurrency);

        // Simulate generation (replace with actual logic)
        const phones = phoneNumbers.split("\n").filter((n) => n.trim());
        const mockResults = phones.map((phone) => ({
            phone: phone.trim(),
            otp: Math.floor(100000 + Math.random() * 900000).toString(),
            status: "success",
        }));
        setResults(mockResults);

        setTimeout(() => {
            setIsRunning(false);
            toast.success(`Successfully generated ${mockResults.length} OTP codes!`);
        }, 2000);
    };

    const handleStop = () => {
        setIsRunning(false);
        toast.warning("OTP generation stopped");
        console.log("Stopping OTP generation...");
    };

    const handleClear = () => {
        setResults([]);
        setPhoneNumbers("");
        toast.info("Cleared all data");
    };

    const handleCopyResults = () => {
        const text = results.map((r) => `${r.phone}:${r.otp}`).join("\n");
        navigator.clipboard.writeText(text);
        toast.success(`Copied ${results.length} results to clipboard!`);
    };

    const handleCopyItem = (index: number, phone: string, otp: string) => {
        const text = `${phone}:${otp}`;
        navigator.clipboard.writeText(text);
        setCopiedIndex(index);

        // Reset the checkmark after 2 seconds
        setTimeout(() => {
            setCopiedIndex(null);
        }, 2000);
    };

    const phoneCount = phoneNumbers.split("\n").filter((n) => n.trim()).length;

    return (
        <Box sx={{height: "100%", display: "flex", flexDirection: "column", overflow: "hidden"}}>
            {/* Header */}
            <Box sx={{px: 6, pt: 5, pb: 3}}>
                <Typography variant="h4" sx={{fontWeight: 700, mb: 1, letterSpacing: "-0.02em"}}>
                    Generate OTP
                </Typography>
                <Typography variant="body2" sx={{color: "text.secondary"}}>
                    Generate OTP codes for multiple phone numbers with advanced concurrency control
                </Typography>
            </Box>

            {/* Control Bar */}
            <Box sx={{px: 6, pb: 3}}>
                <Box
                    sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 3,
                        p: 2.5,
                        bgcolor: "background.paper",
                        borderRadius: 2,
                        border: "1px solid",
                        borderColor: "divider",
                    }}
                >
                    <Box sx={{display: "flex", alignItems: "center", gap: 1.5}}>
                        <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem", fontWeight: 500}}>
                            Concurrency:
                        </Typography>
                        <TextField
                            type="number"
                            value={concurrency}
                            onChange={(e) => setConcurrency(parseInt(e.target.value) || 1)}
                            size="small"
                            inputProps={{min: 1, max: 50}}
                            sx={{
                                width: 90,
                                "& .MuiInputBase-input": {
                                    textAlign: "center",
                                    fontWeight: 600,
                                },
                            }}
                        />
                    </Box>

                    <Divider orientation="vertical" flexItem sx={{opacity: 0.5}} />

                    <Box sx={{display: "flex", alignItems: "center", gap: 1}}>
                        <Box
                            sx={{
                                width: 8,
                                height: 8,
                                borderRadius: "50%",
                                bgcolor: phoneCount > 0 ? "success.main" : "grey.600",
                            }}
                        />
                        <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                            <Typography component="span" sx={{fontWeight: 600, color: "text.primary"}}>
                                {phoneCount}
                            </Typography>{" "}
                            numbers loaded
                        </Typography>
                    </Box>

                    <Box sx={{display: "flex", gap: 1.5, ml: "auto"}}>
                        <Button
                            onClick={handleClear}
                            disabled={isRunning}
                            variant="outlined"
                            size="medium"
                            startIcon={<HiArrowPath size={16} />}
                        >
                            Clear
                        </Button>
                        {isRunning ? (
                            <Button onClick={handleStop} variant="contained" color="error" size="medium" startIcon={<HiStop size={16} />}>
                                Stop
                            </Button>
                        ) : (
                            <Button
                                onClick={handleStart}
                                disabled={phoneCount === 0}
                                variant="contained"
                                size="medium"
                                startIcon={<HiPlay size={16} />}
                            >
                                Start Generation
                            </Button>
                        )}
                    </Box>
                </Box>
            </Box>

            {/* Main Content - Two Panels */}
            <Box sx={{px: 6, pb: 6, flexGrow: 1, display: "flex", gap: 3, overflow: "hidden"}}>
                {/* Left Panel - Phone Numbers Input */}
                <Card sx={{flex: 1, display: "flex", flexDirection: "column", overflow: "hidden"}}>
                    <Box sx={{p: 3, borderBottom: "1px solid", borderColor: "divider"}}>
                        <Typography variant="h6" sx={{fontWeight: 600, mb: 0.5, fontSize: "1rem"}}>
                            Phone Numbers
                        </Typography>
                        <Typography variant="caption" sx={{color: "text.secondary", fontSize: "0.75rem"}}>
                            Enter one phone number per line
                        </Typography>
                    </Box>
                    <Box sx={{flexGrow: 1, p: 3, overflow: "hidden", display: "flex", minHeight: 300}}>
                        <Box
                            sx={{
                                display: "flex",
                                gap: 0,
                                width: "100%",
                                border: "1px solid",
                                borderColor: "divider",
                                borderRadius: 1.5,
                                overflow: "hidden",
                                bgcolor: "background.default",
                                "&:focus-within": {
                                    borderColor: "primary.main",
                                },
                            }}
                        >
                            <SimpleBar style={{width: "100%", height: "100%"}}>
                                <Box sx={{display: "flex", minHeight: "100%"}}>
                                    {/* Line Numbers */}
                                    <Box
                                        sx={{
                                            py: 1.5,
                                            px: 2,
                                            bgcolor: "rgba(255, 255, 255, 0.02)",
                                            borderRight: "1px solid",
                                            borderColor: "divider",
                                            userSelect: "none",
                                        }}
                                    >
                                        {phoneNumbers.split("\n").map((_, index) => (
                                            <Typography
                                                key={index}
                                                sx={{
                                                    fontFamily: "monospace",
                                                    fontSize: "0.875rem",
                                                    lineHeight: 1.6,
                                                    color: "text.secondary",
                                                    opacity: 0.5,
                                                    textAlign: "right",
                                                    minWidth: "2em",
                                                }}
                                            >
                                                {index + 1}
                                            </Typography>
                                        ))}
                                    </Box>

                                    {/* Text Input */}
                                    <TextField
                                        value={phoneNumbers}
                                        onChange={(e) => setPhoneNumbers(e.target.value)}
                                        placeholder="Enter phone numbers (one per line)&#10;&#10;Example:&#10;+1234567890&#10;+0987654321&#10;+1122334455"
                                        multiline
                                        fullWidth
                                        sx={{
                                            flex: 1,
                                            "& .MuiInputBase-root": {
                                                alignItems: "flex-start",
                                                padding: 0,
                                            },
                                            "& .MuiOutlinedInput-notchedOutline": {
                                                border: "none",
                                            },
                                            "& .MuiInputBase-input": {
                                                fontFamily: "monospace",
                                                fontSize: "0.875rem",
                                                lineHeight: 1.6,
                                                padding: "12px 16px",
                                            },
                                        }}
                                    />
                                </Box>
                            </SimpleBar>
                        </Box>
                    </Box>

                    {/* Input Stats & Quick Actions */}
                    <Box
                        sx={{
                            p: 2,
                            borderTop: "1px solid",
                            borderColor: "divider",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            bgcolor: "rgba(255, 255, 255, 0.01)",
                        }}
                    >
                        <Box sx={{display: "flex", alignItems: "center", gap: 3}}>
                            <Box sx={{display: "flex", alignItems: "center", gap: 1}}>
                                <Typography variant="caption" sx={{color: "text.secondary", fontSize: "0.75rem"}}>
                                    Lines:
                                </Typography>
                                <Typography variant="caption" sx={{fontWeight: 600, fontSize: "0.75rem"}}>
                                    {phoneNumbers.split("\n").length}
                                </Typography>
                            </Box>
                            <Box sx={{display: "flex", alignItems: "center", gap: 1}}>
                                <Typography variant="caption" sx={{color: "text.secondary", fontSize: "0.75rem"}}>
                                    Valid:
                                </Typography>
                                <Typography variant="caption" sx={{fontWeight: 600, fontSize: "0.75rem", color: "success.main"}}>
                                    {phoneCount}
                                </Typography>
                            </Box>
                            <Box sx={{display: "flex", alignItems: "center", gap: 1}}>
                                <Typography variant="caption" sx={{color: "text.secondary", fontSize: "0.75rem"}}>
                                    Empty:
                                </Typography>
                                <Typography variant="caption" sx={{fontWeight: 600, fontSize: "0.75rem", color: "text.secondary"}}>
                                    {phoneNumbers.split("\n").length - phoneCount}
                                </Typography>
                            </Box>
                        </Box>
                        <Box sx={{display: "flex", gap: 0.5}}>
                            <Tooltip title="Clean Up - Remove empty lines" arrow placement="top">
                                <span>
                                    <IconButton
                                        onClick={() => {
                                            // Remove empty lines
                                            const cleaned = phoneNumbers
                                                .split("\n")
                                                .filter((line) => line.trim())
                                                .join("\n");
                                            setPhoneNumbers(cleaned);
                                            toast.success("Removed empty lines");
                                        }}
                                        disabled={phoneNumbers.split("\n").length === phoneCount}
                                        size="small"
                                        sx={{
                                            fontSize: "0.75rem",
                                            "&:hover": {
                                                bgcolor: "rgba(99, 102, 241, 0.1)",
                                            },
                                        }}
                                    >
                                        <HiSparkles size={16} />
                                    </IconButton>
                                </span>
                            </Tooltip>
                            <Tooltip title="Remove Duplicates" arrow placement="top">
                                <IconButton
                                    onClick={() => {
                                        // Remove duplicates
                                        const lines = phoneNumbers.split("\n").filter((line) => line.trim());
                                        const unique = [...new Set(lines)];
                                        setPhoneNumbers(unique.join("\n"));
                                        toast.success(`Removed ${lines.length - unique.length} duplicates`);
                                    }}
                                    size="small"
                                    sx={{
                                        fontSize: "0.75rem",
                                        "&:hover": {
                                            bgcolor: "rgba(99, 102, 241, 0.1)",
                                        },
                                    }}
                                >
                                    <HiXMark size={16} />
                                </IconButton>
                            </Tooltip>
                        </Box>
                    </Box>
                </Card>

                {/* Right Panel - Results */}
                <Card sx={{flex: 1, display: "flex", flexDirection: "column", overflow: "hidden"}}>
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
                        <Box>
                            <Typography variant="h6" sx={{fontWeight: 600, mb: 0.5, fontSize: "1rem"}}>
                                Results
                            </Typography>
                            <Typography variant="caption" sx={{color: "text.secondary", fontSize: "0.75rem"}}>
                                {results.length > 0 ? `${results.length} OTP codes generated` : "No results yet"}
                            </Typography>
                        </Box>
                        {results.length > 0 && (
                            <Button
                                onClick={handleCopyResults}
                                variant="outlined"
                                size="small"
                                startIcon={<HiClipboardDocument size={16} />}
                            >
                                Copy All
                            </Button>
                        )}
                    </Box>
                    <Box sx={{flexGrow: 1, p: 3, overflow: "hidden"}}>
                        <SimpleBar style={{maxHeight: "100%", height: "100%"}}>
                            {results.length === 0 ? (
                                <Box
                                    sx={{
                                        height: "100%",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
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
                                            <HiClipboardDocument size={32} style={{opacity: 0.4}} />
                                        </Box>
                                        <Typography variant="body2" sx={{color: "text.secondary"}}>
                                            Results will appear here
                                        </Typography>
                                    </Box>
                                </Box>
                            ) : (
                                <Box sx={{display: "flex", flexDirection: "column", gap: 1.5}}>
                                    {results.map((result, index) => (
                                        <Box
                                            key={index}
                                            onClick={() => handleCopyItem(index, result.phone, result.otp)}
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
                                                <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
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
                                            <Typography
                                                variant="h6"
                                                sx={{
                                                    fontFamily: "monospace",
                                                    fontWeight: 700,
                                                    color: "primary.main",
                                                    fontSize: "1.25rem",
                                                    letterSpacing: "0.15em",
                                                }}
                                            >
                                                {result.otp}
                                            </Typography>
                                        </Box>
                                    ))}
                                </Box>
                            )}
                        </SimpleBar>
                    </Box>
                </Card>
            </Box>
        </Box>
    );
}
