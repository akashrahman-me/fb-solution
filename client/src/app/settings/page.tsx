"use client";
import React, {useState, useEffect} from "react";
import SimpleBar from "simplebar-react";
import "simplebar-react/dist/simplebar.min.css";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Switch from "@mui/material/Switch";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import {toast} from "react-toastify";
import {useTheme} from "@/context/ThemeContext";

export default function SettingsPage() {
    const {themeMode, setThemeMode} = useTheme();
    const [autoCopy, setAutoCopy] = useState<boolean>(false);
    const [saveHistory, setSaveHistory] = useState<boolean>(true);
    const [showNotifications, setShowNotifications] = useState<boolean>(true);
    const [defaultConcurrency, setDefaultConcurrency] = useState<number>(5);
    const [isLoaded, setIsLoaded] = useState(false);
    const [previousTheme, setPreviousTheme] = useState<string>(themeMode);

    // Load settings from localStorage on mount
    useEffect(() => {
        if (typeof window !== "undefined") {
            const savedAutoCopy = localStorage.getItem("autoCopy");
            const savedHistory = localStorage.getItem("saveHistory");
            const savedNotifications = localStorage.getItem("showNotifications");
            const savedConcurrency = localStorage.getItem("defaultConcurrency");

            setAutoCopy(savedAutoCopy === "true");
            setSaveHistory(savedHistory !== null ? savedHistory === "true" : true);
            setShowNotifications(savedNotifications !== null ? savedNotifications === "true" : true);
            setDefaultConcurrency(savedConcurrency ? parseInt(savedConcurrency) : 5);
            setPreviousTheme(themeMode); // Set initial theme
            setIsLoaded(true);
        }
    }, [themeMode]);

    // Show toast ONLY when theme actually changes (not on initial load)
    useEffect(() => {
        if (isLoaded && previousTheme !== themeMode) {
            toast.success(
                `Theme changed to ${themeMode === "system" ? "System Default" : themeMode === "dark" ? "Dark Mode" : "Light Mode"}`
            );
            setPreviousTheme(themeMode);
        }
    }, [themeMode, isLoaded, previousTheme]);

    // Auto-save other settings
    useEffect(() => {
        if (isLoaded) {
            localStorage.setItem("autoCopy", autoCopy.toString());
        }
    }, [autoCopy, isLoaded]);

    useEffect(() => {
        if (isLoaded) {
            localStorage.setItem("saveHistory", saveHistory.toString());
        }
    }, [saveHistory, isLoaded]);

    useEffect(() => {
        if (isLoaded) {
            localStorage.setItem("showNotifications", showNotifications.toString());
        }
    }, [showNotifications, isLoaded]);

    useEffect(() => {
        if (isLoaded) {
            localStorage.setItem("defaultConcurrency", defaultConcurrency.toString());
        }
    }, [defaultConcurrency, isLoaded]);

    const handleClearData = () => {
        if (window.confirm("Are you sure you want to clear all data? This action cannot be undone.")) {
            localStorage.clear();
            toast.success("All data cleared successfully");
            // Reload settings
            setThemeMode("system");
            setAutoCopy(false);
            setSaveHistory(true);
            setShowNotifications(true);
            setDefaultConcurrency(5);
        }
    };
    return (
        <Box sx={{height: "100%", display: "flex", flexDirection: "column", overflow: "hidden"}}>
            <SimpleBar style={{maxHeight: "100%", height: "100%"}}>
                {/* Header */}
                <Box sx={{px: 6, pt: 5, pb: 3}}>
                    <Typography variant="h4" sx={{fontWeight: 700, mb: 1, letterSpacing: "-0.02em"}}>
                        Settings
                    </Typography>
                    <Typography variant="body2" sx={{color: "text.secondary"}}>
                        Configure your application preferences and behavior
                    </Typography>
                </Box>

                {/* Settings Content */}
                <Box sx={{px: 6, pb: 6, maxWidth: 900}}>
                    <Box sx={{display: "flex", flexDirection: "column", gap: 3}}>
                        {/* General Settings */}
                        <Card>
                            <CardContent sx={{p: 4}}>
                                <Typography variant="h6" sx={{fontWeight: 600, mb: 3, fontSize: "1rem"}}>
                                    General Settings
                                </Typography>

                                <Box sx={{display: "flex", flexDirection: "column", gap: 0}}>
                                    <Box
                                        sx={{
                                            display: "flex",
                                            alignItems: "center",
                                            justifyContent: "space-between",
                                            py: 2.5,
                                        }}
                                    >
                                        <Box sx={{flex: 1}}>
                                            <Typography variant="body1" sx={{fontWeight: 600, mb: 0.5}}>
                                                Auto-copy OTP
                                            </Typography>
                                            <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                                                Automatically copy generated OTP codes to your clipboard
                                            </Typography>
                                        </Box>
                                        <Switch checked={autoCopy} onChange={(e) => setAutoCopy(e.target.checked)} />
                                    </Box>

                                    <Divider sx={{opacity: 0.5}} />

                                    <Box
                                        sx={{
                                            display: "flex",
                                            alignItems: "center",
                                            justifyContent: "space-between",
                                            py: 2.5,
                                        }}
                                    >
                                        <Box sx={{flex: 1}}>
                                            <Typography variant="body1" sx={{fontWeight: 600, mb: 0.5}}>
                                                Save History
                                            </Typography>
                                            <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                                                Store generated OTP codes in application history
                                            </Typography>
                                        </Box>
                                        <Switch checked={saveHistory} onChange={(e) => setSaveHistory(e.target.checked)} />
                                    </Box>

                                    <Divider sx={{opacity: 0.5}} />

                                    <Box
                                        sx={{
                                            display: "flex",
                                            alignItems: "center",
                                            justifyContent: "space-between",
                                            py: 2.5,
                                        }}
                                    >
                                        <Box sx={{flex: 1}}>
                                            <Typography variant="body1" sx={{fontWeight: 600, mb: 0.5}}>
                                                Show Notifications
                                            </Typography>
                                            <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                                                Display system notifications for important events
                                            </Typography>
                                        </Box>
                                        <Switch checked={showNotifications} onChange={(e) => setShowNotifications(e.target.checked)} />
                                    </Box>
                                </Box>
                            </CardContent>
                        </Card>

                        {/* Appearance */}
                        <Card>
                            <CardContent sx={{p: 4}}>
                                <Typography variant="h6" sx={{fontWeight: 600, mb: 3, fontSize: "1rem"}}>
                                    Appearance
                                </Typography>

                                <Box>
                                    <Typography variant="body2" sx={{fontWeight: 600, mb: 1.5, fontSize: "0.8125rem"}}>
                                        Theme Mode
                                    </Typography>
                                    <Select
                                        fullWidth
                                        value={themeMode}
                                        onChange={(e) => setThemeMode(e.target.value as "dark" | "light" | "system")}
                                        size="small"
                                        sx={{maxWidth: 300}}
                                    >
                                        <MenuItem value="system">System Default</MenuItem>
                                        <MenuItem value="dark">Dark Mode</MenuItem>
                                        <MenuItem value="light">Light Mode</MenuItem>
                                    </Select>
                                    <Typography
                                        variant="caption"
                                        sx={{color: "text.secondary", display: "block", mt: 1, fontSize: "0.75rem"}}
                                    >
                                        Choose your preferred color scheme
                                    </Typography>
                                </Box>
                            </CardContent>
                        </Card>

                        {/* Advanced */}
                        <Card>
                            <CardContent sx={{p: 4}}>
                                <Typography variant="h6" sx={{fontWeight: 600, mb: 3, fontSize: "1rem"}}>
                                    Advanced
                                </Typography>

                                <Box sx={{display: "flex", flexDirection: "column", gap: 2.5}}>
                                    <Box>
                                        <Typography variant="body2" sx={{fontWeight: 600, mb: 1.5, fontSize: "0.8125rem"}}>
                                            Default Concurrency
                                        </Typography>
                                        <Select
                                            fullWidth
                                            value={defaultConcurrency}
                                            onChange={(e) => setDefaultConcurrency(e.target.value as number)}
                                            size="small"
                                            sx={{maxWidth: 300}}
                                        >
                                            <MenuItem value={1}>1 Thread</MenuItem>
                                            <MenuItem value={3}>3 Threads</MenuItem>
                                            <MenuItem value={5}>5 Threads</MenuItem>
                                            <MenuItem value={10}>10 Threads</MenuItem>
                                            <MenuItem value={20}>20 Threads</MenuItem>
                                        </Select>
                                        <Typography
                                            variant="caption"
                                            sx={{color: "text.secondary", display: "block", mt: 1, fontSize: "0.75rem"}}
                                        >
                                            Number of concurrent OTP generation operations
                                        </Typography>
                                    </Box>

                                    <Divider sx={{opacity: 0.5}} />

                                    <Box>
                                        <Button variant="outlined" color="error" fullWidth sx={{maxWidth: 300}} onClick={handleClearData}>
                                            Clear All Data
                                        </Button>
                                        <Typography
                                            variant="caption"
                                            sx={{color: "text.secondary", display: "block", mt: 1, fontSize: "0.75rem"}}
                                        >
                                            Remove all saved history and application data
                                        </Typography>
                                    </Box>
                                </Box>
                            </CardContent>
                        </Card>

                        {/* About */}
                        <Card>
                            <CardContent sx={{p: 4}}>
                                <Typography variant="h6" sx={{fontWeight: 600, mb: 3, fontSize: "1rem"}}>
                                    About
                                </Typography>
                                <Box sx={{display: "flex", flexDirection: "column", gap: 2}}>
                                    <Box sx={{display: "flex", alignItems: "center", justifyContent: "space-between", py: 1}}>
                                        <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                                            Version
                                        </Typography>
                                        <Typography variant="body2" sx={{fontWeight: 600, fontSize: "0.8125rem"}}>
                                            0.1.0
                                        </Typography>
                                    </Box>
                                    <Divider sx={{opacity: 0.5}} />
                                    <Box sx={{display: "flex", alignItems: "center", justifyContent: "space-between", py: 1}}>
                                        <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                                            Developer
                                        </Typography>
                                        <Typography variant="body2" sx={{fontWeight: 600, fontSize: "0.8125rem"}}>
                                            FB OTP Team
                                        </Typography>
                                    </Box>
                                    <Divider sx={{opacity: 0.5}} />
                                    <Box sx={{display: "flex", alignItems: "center", justifyContent: "space-between", py: 1}}>
                                        <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                                            License
                                        </Typography>
                                        <Typography variant="body2" sx={{fontWeight: 600, fontSize: "0.8125rem"}}>
                                            MIT License
                                        </Typography>
                                    </Box>
                                </Box>
                            </CardContent>
                        </Card>
                    </Box>
                </Box>
            </SimpleBar>
        </Box>
    );
}
