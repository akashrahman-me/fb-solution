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
import TextField from "@mui/material/TextField";
import Divider from "@mui/material/Divider";
import CircularProgress from "@mui/material/CircularProgress";
import {toast} from "react-toastify";
import {useTheme} from "@/context/ThemeContext";
import {getProxyConfig, setProxyConfig} from "@/services/api";
import {ProxyConfig} from "@/types/api";

export default function SettingsPage() {
    const {themeMode, setThemeMode} = useTheme();
    const [isLoaded, setIsLoaded] = useState(false);
    const [previousTheme, setPreviousTheme] = useState<string>(themeMode);

    // Proxy settings
    const [proxyConfig, setProxyConfigState] = useState<ProxyConfig>({
        enabled: false,
        server: "",
        port: 8080,
        username: "",
        password: "",
    });
    const [proxyLoading, setProxyLoading] = useState(false);

    // Load proxy configuration
    useEffect(() => {
        loadProxyConfig();
    }, []);

    const loadProxyConfig = async () => {
        try {
            // First, try to load from localStorage
            const localConfig = localStorage.getItem("fb-checker-proxy-config");
            if (localConfig) {
                const parsed = JSON.parse(localConfig);
                setProxyConfigState({
                    enabled: parsed.enabled ?? false,
                    server: parsed.server ?? "",
                    port: parsed.port ?? 8080,
                    username: parsed.username ?? "",
                    password: parsed.password ?? "",
                });
            }

            // Then sync with backend
            const response = await getProxyConfig();
            if (response.success && response.data) {
                const config = {
                    enabled: response.data.enabled ?? false,
                    server: response.data.server ?? "",
                    port: response.data.port ?? 8080,
                    username: response.data.username ?? "",
                    password: response.data.password ?? "",
                };
                setProxyConfigState(config);
                // Save to localStorage
                localStorage.setItem("fb-checker-proxy-config", JSON.stringify(config));
            }
        } catch (error) {
            console.error("Error loading proxy config:", error);
        }
    };

    const handleSaveProxy = async () => {
        setProxyLoading(true);
        try {
            const response = await setProxyConfig(proxyConfig);
            if (response.success) {
                // Save to localStorage on success
                localStorage.setItem("fb-checker-proxy-config", JSON.stringify(proxyConfig));
                toast.success("Proxy configuration saved successfully");
            } else {
                toast.error(response.error || "Failed to save proxy configuration");
            }
        } catch (error) {
            console.error("Error saving proxy config:", error);
            toast.error("Failed to save proxy configuration");
        } finally {
            setProxyLoading(false);
        }
    };

    // Auto-save proxy config to localStorage when it changes
    useEffect(() => {
        if (isLoaded) {
            localStorage.setItem("fb-checker-proxy-config", JSON.stringify(proxyConfig));
        }
    }, [proxyConfig, isLoaded]);

    // Load settings from localStorage on mount
    useEffect(() => {
        if (typeof window !== "undefined") {
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

                        {/* Proxy Configuration */}
                        <Card>
                            <CardContent sx={{p: 4}}>
                                <Typography variant="h6" sx={{fontWeight: 600, mb: 3, fontSize: "1rem"}}>
                                    Proxy Configuration
                                </Typography>

                                <Box sx={{display: "flex", flexDirection: "column", gap: 2.5}}>
                                    <Box
                                        sx={{
                                            display: "flex",
                                            alignItems: "center",
                                            justifyContent: "space-between",
                                            pb: 2,
                                        }}
                                    >
                                        <Box sx={{flex: 1}}>
                                            <Typography variant="body1" sx={{fontWeight: 600, mb: 0.5}}>
                                                Enable Proxy
                                            </Typography>
                                            <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem"}}>
                                                Route requests through a proxy server
                                            </Typography>
                                        </Box>
                                        <Switch
                                            checked={proxyConfig.enabled}
                                            onChange={(e) => setProxyConfigState({...proxyConfig, enabled: e.target.checked})}
                                        />
                                    </Box>

                                    {proxyConfig.enabled && (
                                        <>
                                            <Box>
                                                <Typography variant="body2" sx={{fontWeight: 600, mb: 1.5, fontSize: "0.8125rem"}}>
                                                    Proxy Server
                                                </Typography>
                                                <TextField
                                                    fullWidth
                                                    value={proxyConfig.server}
                                                    onChange={(e) => setProxyConfigState({...proxyConfig, server: e.target.value})}
                                                    placeholder="e.g., 31.59.20.176"
                                                    size="small"
                                                    sx={{maxWidth: 400}}
                                                />
                                            </Box>

                                            <Box>
                                                <Typography variant="body2" sx={{fontWeight: 600, mb: 1.5, fontSize: "0.8125rem"}}>
                                                    Port
                                                </Typography>
                                                <TextField
                                                    fullWidth
                                                    type="number"
                                                    value={proxyConfig.port}
                                                    onChange={(e) =>
                                                        setProxyConfigState({...proxyConfig, port: parseInt(e.target.value) || 8080})
                                                    }
                                                    placeholder="e.g., 8080"
                                                    size="small"
                                                    sx={{maxWidth: 200}}
                                                />
                                            </Box>

                                            <Box>
                                                <Typography variant="body2" sx={{fontWeight: 600, mb: 1.5, fontSize: "0.8125rem"}}>
                                                    Username (Optional)
                                                </Typography>
                                                <TextField
                                                    fullWidth
                                                    value={proxyConfig.username || ""}
                                                    onChange={(e) => setProxyConfigState({...proxyConfig, username: e.target.value})}
                                                    placeholder="Proxy username"
                                                    size="small"
                                                    sx={{maxWidth: 400}}
                                                />
                                            </Box>

                                            <Box>
                                                <Typography variant="body2" sx={{fontWeight: 600, mb: 1.5, fontSize: "0.8125rem"}}>
                                                    Password (Optional)
                                                </Typography>
                                                <TextField
                                                    fullWidth
                                                    type="password"
                                                    value={proxyConfig.password || ""}
                                                    onChange={(e) => setProxyConfigState({...proxyConfig, password: e.target.value})}
                                                    placeholder="Proxy password"
                                                    size="small"
                                                    sx={{maxWidth: 400}}
                                                />
                                            </Box>

                                            <Divider sx={{opacity: 0.5}} />

                                            <Box sx={{display: "flex", gap: 2}}>
                                                <Button
                                                    variant="contained"
                                                    onClick={handleSaveProxy}
                                                    disabled={proxyLoading}
                                                    startIcon={proxyLoading && <CircularProgress size={16} />}
                                                >
                                                    {proxyLoading ? "Saving..." : "Save Proxy"}
                                                </Button>
                                            </Box>
                                        </>
                                    )}
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
