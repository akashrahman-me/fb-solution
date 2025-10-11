"use client";

/**
 * ThemeContext - Centralized Theme Management for MUI v7
 *
 * This context provides:
 * 1. Theme mode management (dark/light/system)
 * 2. System preference detection and auto-switching
 * 3. localStorage persistence
 * 4. Complete MUI theme configuration following v7 best practices
 *
 * Usage:
 * - Wrap app with <ThemeProvider> in layout.tsx
 * - Use useTheme() hook to access themeMode, setThemeMode, actualTheme
 *
 * MUI v7 Structure:
 * - palette.mode controls dark/light theme
 * - palette contains colors for both modes
 * - components.styleOverrides customizes component styles
 * - actualTheme is used for conditional styling in styleOverrides
 */

import React, {createContext, useContext, useEffect, useState, ReactNode} from "react";
import {ThemeProvider as MUIThemeProvider, createTheme} from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";

type ThemeMode = "dark" | "light" | "system";

interface ThemeContextType {
    themeMode: ThemeMode;
    setThemeMode: (mode: ThemeMode) => void;
    actualTheme: "dark" | "light";
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error("useTheme must be used within ThemeProvider");
    }
    return context;
};

interface ThemeProviderProps {
    children: ReactNode;
}

export function ThemeProvider({children}: ThemeProviderProps) {
    const [themeMode, setThemeMode] = useState<ThemeMode>("system");
    const [actualTheme, setActualTheme] = useState<"dark" | "light">("dark");

    // Load theme from localStorage on mount
    useEffect(() => {
        if (typeof window !== "undefined") {
            const savedTheme = localStorage.getItem("themeMode") as ThemeMode;
            if (savedTheme) {
                setThemeMode(savedTheme);
            }
        }
    }, []);

    // Determine actual theme based on mode and system preference
    useEffect(() => {
        if (typeof window !== "undefined") {
            let theme: "dark" | "light" = "dark";

            if (themeMode === "system") {
                const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
                theme = prefersDark ? "dark" : "light";

                // Listen for system theme changes
                const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
                const handleChange = (e: MediaQueryListEvent) => {
                    setActualTheme(e.matches ? "dark" : "light");
                };
                mediaQuery.addEventListener("change", handleChange);
                return () => mediaQuery.removeEventListener("change", handleChange);
            } else {
                theme = themeMode;
            }

            setActualTheme(theme);
            localStorage.setItem("themeMode", themeMode);
        }
    }, [themeMode]);

    // Create MUI theme based on actual theme - following MUI v7 best practices
    const muiTheme = createTheme({
        palette: {
            mode: actualTheme,
            primary: {
                main: "#6366f1",
                light: "#818cf8",
                dark: "#4f46e5",
            },
            secondary: {
                main: "#8b5cf6",
                light: "#a78bfa",
                dark: "#7c3aed",
            },
            success: {
                main: "#10b981",
                light: "#34d399",
                dark: "#059669",
            },
            warning: {
                main: "#f59e0b",
                light: "#fbbf24",
                dark: "#d97706",
            },
            error: {
                main: "#ef4444",
                light: "#f87171",
                dark: "#dc2626",
            },
            ...(actualTheme === "dark"
                ? {
                      background: {
                          default: "#0f0f1a",
                          paper: "#1a1a2e",
                      },
                      divider: "rgba(255, 255, 255, 0.05)",
                      text: {
                          primary: "#e5e7eb",
                          secondary: "#9ca3af",
                      },
                  }
                : {
                      background: {
                          default: "#f8f9fa",
                          paper: "#ffffff",
                      },
                      divider: "rgba(0, 0, 0, 0.12)",
                      text: {
                          primary: "rgba(0, 0, 0, 0.87)",
                          secondary: "rgba(0, 0, 0, 0.6)",
                      },
                  }),
        },
        typography: {
            fontFamily: 'var(--font-geist-sans), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
            button: {
                textTransform: "none",
                fontWeight: 500,
            },
            h1: {
                fontSize: "2rem",
                fontWeight: 600,
                letterSpacing: "-0.02em",
            },
            h2: {
                fontSize: "1.5rem",
                fontWeight: 600,
                letterSpacing: "-0.01em",
            },
            h5: {
                fontSize: "1.125rem",
                fontWeight: 600,
            },
            h6: {
                fontSize: "1rem",
                fontWeight: 600,
            },
            body1: {
                fontSize: "0.9375rem",
            },
            body2: {
                fontSize: "0.875rem",
            },
        },
        shape: {
            borderRadius: 8,
        },
        components: {
            MuiButton: {
                styleOverrides: {
                    root: {
                        borderRadius: 8,
                        padding: "8px 16px",
                        fontWeight: 500,
                        boxShadow: "none",
                        "&:hover": {
                            boxShadow: "none",
                        },
                    },
                    contained: {
                        background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                        "&:hover": {
                            background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
                        },
                    },
                    outlined: {
                        borderColor: actualTheme === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.23)",
                        "&:hover": {
                            borderColor: actualTheme === "dark" ? "rgba(255, 255, 255, 0.2)" : "rgba(0, 0, 0, 0.4)",
                            backgroundColor: actualTheme === "dark" ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.04)",
                        },
                    },
                },
            },
            MuiCard: {
                styleOverrides: {
                    root: {
                        backgroundImage: "none",
                        backgroundColor: actualTheme === "dark" ? "#1a1a2e" : "#ffffff",
                        border: actualTheme === "dark" ? "1px solid rgba(255, 255, 255, 0.05)" : "1px solid rgba(0, 0, 0, 0.12)",
                        borderRadius: 12,
                        transition: "all 0.2s ease",
                        "&:hover": {
                            borderColor: actualTheme === "dark" ? "rgba(99, 102, 241, 0.3)" : "rgba(99, 102, 241, 0.5)",
                            boxShadow: actualTheme === "dark" ? "0 4px 20px rgba(99, 102, 241, 0.1)" : "0 4px 20px rgba(99, 102, 241, 0.2)",
                        },
                    },
                },
            },
            MuiTextField: {
                styleOverrides: {
                    root: {
                        "& .MuiOutlinedInput-root": {
                            backgroundColor: actualTheme === "dark" ? "#0f0f1a" : "#ffffff",
                            borderRadius: 8,
                            "& fieldset": {
                                borderColor: actualTheme === "dark" ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.23)",
                            },
                            "&:hover fieldset": {
                                borderColor: actualTheme === "dark" ? "rgba(255, 255, 255, 0.15)" : "rgba(0, 0, 0, 0.4)",
                            },
                            "&.Mui-focused fieldset": {
                                borderColor: "#6366f1",
                                borderWidth: "1px",
                            },
                        },
                    },
                },
            },
            MuiSelect: {
                styleOverrides: {
                    root: {
                        backgroundColor: actualTheme === "dark" ? "#0f0f1a" : "#ffffff",
                        borderRadius: 8,
                        "& fieldset": {
                            borderColor: actualTheme === "dark" ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.23)",
                        },
                        "&:hover fieldset": {
                            borderColor: actualTheme === "dark" ? "rgba(255, 255, 255, 0.15)" : "rgba(0, 0, 0, 0.4)",
                        },
                        "&.Mui-focused fieldset": {
                            borderColor: "#6366f1",
                        },
                    },
                },
            },
            MuiChip: {
                styleOverrides: {
                    root: {
                        borderRadius: 6,
                        fontWeight: 500,
                        fontSize: "0.75rem",
                    },
                    colorSuccess: {
                        backgroundColor: "rgba(16, 185, 129, 0.15)",
                        color: "#10b981",
                        border: "1px solid rgba(16, 185, 129, 0.2)",
                    },
                    colorError: {
                        backgroundColor: "rgba(239, 68, 68, 0.15)",
                        color: "#ef4444",
                        border: "1px solid rgba(239, 68, 68, 0.2)",
                    },
                },
            },
            MuiListItemButton: {
                styleOverrides: {
                    root: {
                        borderRadius: 8,
                        marginBottom: 4,
                        transition: "all 0.2s ease",
                        "&:hover": {
                            backgroundColor: actualTheme === "dark" ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.04)",
                        },
                        "&.Mui-selected": {
                            backgroundColor: actualTheme === "dark" ? "rgba(99, 102, 241, 0.15)" : "rgba(99, 102, 241, 0.1)",
                            borderLeft: "3px solid #6366f1",
                            "&:hover": {
                                backgroundColor: actualTheme === "dark" ? "rgba(99, 102, 241, 0.2)" : "rgba(99, 102, 241, 0.15)",
                            },
                        },
                    },
                },
            },
            MuiIconButton: {
                styleOverrides: {
                    root: {
                        borderRadius: 8,
                        "&:hover": {
                            backgroundColor: actualTheme === "dark" ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.04)",
                        },
                    },
                },
            },
            MuiSwitch: {
                styleOverrides: {
                    root: {
                        width: 42,
                        height: 24,
                        padding: 0,
                    },
                    switchBase: {
                        padding: 3,
                        "&.Mui-checked": {
                            transform: "translateX(18px)",
                            "& + .MuiSwitch-track": {
                                backgroundColor: "#6366f1",
                                opacity: 1,
                            },
                        },
                    },
                    thumb: {
                        width: 18,
                        height: 18,
                    },
                    track: {
                        borderRadius: 12,
                        backgroundColor: actualTheme === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.26)",
                        opacity: 1,
                    },
                },
            },
        },
    });

    return (
        <ThemeContext.Provider value={{themeMode, setThemeMode, actualTheme}}>
            <MUIThemeProvider theme={muiTheme}>
                <CssBaseline />
                {children}
            </MUIThemeProvider>
        </ThemeContext.Provider>
    );
}
