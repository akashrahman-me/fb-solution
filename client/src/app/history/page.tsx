"use client";
import React, {useState, useMemo} from "react";
import {HiMagnifyingGlass, HiTrash, HiClipboardDocument, HiCheck, HiFunnel, HiArrowDownTray} from "react-icons/hi2";
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

interface HistoryItem {
    id: number;
    phone: string;
    otp: string;
    status: "success" | "failed";
    timestamp: string;
    date: Date;
}

export default function HistoryPage() {
    // Mock data - In production, this would come from local storage or a database
    const [historyItems, setHistoryItems] = useState<HistoryItem[]>([
        {
            id: 1,
            phone: "+1234567890",
            otp: "123456",
            status: "success",
            timestamp: "2025-10-11 10:30 AM",
            date: new Date("2025-10-11 10:30"),
        },
        {
            id: 2,
            phone: "+0987654321",
            otp: "789012",
            status: "success",
            timestamp: "2025-10-11 09:15 AM",
            date: new Date("2025-10-11 09:15"),
        },
        {
            id: 3,
            phone: "+1122334455",
            otp: "345678",
            status: "failed",
            timestamp: "2025-10-10 04:20 PM",
            date: new Date("2025-10-10 16:20"),
        },
        {
            id: 4,
            phone: "+5544332211",
            otp: "901234",
            status: "success",
            timestamp: "2025-10-10 02:15 PM",
            date: new Date("2025-10-10 14:15"),
        },
        {
            id: 5,
            phone: "+9988776655",
            otp: "567890",
            status: "success",
            timestamp: "2025-10-09 11:45 AM",
            date: new Date("2025-10-09 11:45"),
        },
    ]);

    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState<"all" | "success" | "failed">("all");
    const [copiedId, setCopiedId] = useState<number | null>(null);

    // Filter and search logic
    const filteredItems = useMemo(() => {
        return historyItems.filter((item) => {
            const matchesSearch = item.phone.toLowerCase().includes(searchQuery.toLowerCase()) || item.otp.includes(searchQuery);
            const matchesStatus = statusFilter === "all" || item.status === statusFilter;
            return matchesSearch && matchesStatus;
        });
    }, [historyItems, searchQuery, statusFilter]);

    const handleCopyItem = (id: number, phone: string, otp: string) => {
        const text = `${phone}:${otp}`;
        navigator.clipboard.writeText(text);
        setCopiedId(id);

        setTimeout(() => {
            setCopiedId(null);
        }, 2000);
    };

    const handleDeleteItem = (id: number) => {
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
            "Phone,OTP,Status,Timestamp",
            ...filteredItems.map((item) => `${item.phone},${item.otp},${item.status},${item.timestamp}`),
        ].join("\n");

        const blob = new Blob([csv], {type: "text/csv"});
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `otp-history-${new Date().toISOString().split("T")[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success("History exported successfully");
    };

    const stats = {
        total: historyItems.length,
        success: historyItems.filter((i) => i.status === "success").length,
        failed: historyItems.filter((i) => i.status === "failed").length,
    };

    return (
        <Box sx={{height: "100%", display: "flex", flexDirection: "column", overflow: "hidden"}}>
            <SimpleBar style={{maxHeight: "100%", height: "100%"}}>
                {/* Header - Static */}
                <Box sx={{px: 6, pt: 5, pb: 3}}>
                    <Typography variant="h4" sx={{fontWeight: 700, mb: 1, letterSpacing: "-0.02em"}}>
                        OTP History
                    </Typography>
                    <Typography variant="body2" sx={{color: "text.secondary"}}>
                        View and manage your previously generated OTP codes
                    </Typography>
                </Box>

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
                                    Total Generated
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
                                    Successful
                                </Typography>
                                <Typography variant="h3" sx={{mt: 1.5, fontWeight: 700, fontSize: "2.25rem", color: "success.main"}}>
                                    {stats.success}
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
                                    Failed
                                </Typography>
                                <Typography variant="h3" sx={{mt: 1.5, fontWeight: 700, fontSize: "2.25rem", color: "error.main"}}>
                                    {stats.failed}
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
                                onChange={(e) => setStatusFilter(e.target.value as "all" | "success" | "failed")}
                                size="small"
                                sx={{minWidth: 130}}
                            >
                                <MenuItem value="all">All Status</MenuItem>
                                <MenuItem value="success">Success</MenuItem>
                                <MenuItem value="failed">Failed</MenuItem>
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
                                            </Box>
                                            <Box sx={{display: "flex", alignItems: "center", gap: 4}}>
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
                                                        OTP Code
                                                    </Typography>
                                                    <Typography
                                                        variant="h6"
                                                        sx={{
                                                            fontFamily: "monospace",
                                                            fontWeight: 700,
                                                            color: "primary.main",
                                                            fontSize: "1.125rem",
                                                            letterSpacing: "0.15em",
                                                        }}
                                                    >
                                                        {item.otp}
                                                    </Typography>
                                                </Box>
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
                                                        Generated
                                                    </Typography>
                                                    <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                                                        {item.timestamp}
                                                    </Typography>
                                                </Box>
                                            </Box>
                                        </Box>
                                        <Box sx={{display: "flex", alignItems: "center", gap: 1}}>
                                            <IconButton
                                                onClick={() => handleCopyItem(item.id, item.phone, item.otp)}
                                                size="small"
                                                title="Copy"
                                            >
                                                {copiedId === item.id ? (
                                                    <HiCheck size={18} style={{color: "#10b981"}} />
                                                ) : (
                                                    <HiClipboardDocument size={18} style={{opacity: 0.6}} />
                                                )}
                                            </IconButton>
                                            <IconButton onClick={() => handleDeleteItem(item.id)} size="small" color="error" title="Delete">
                                                <HiTrash size={18} />
                                            </IconButton>
                                        </Box>
                                    </Box>
                                </Box>
                            ))}
                        </Box>
                    )}
                </Box>
            </SimpleBar>
        </Box>
    );
}
