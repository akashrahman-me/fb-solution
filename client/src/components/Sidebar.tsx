"use client";
import React from "react";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {HiSquares2X2, HiLockClosed, HiClock, HiCog6Tooth} from "react-icons/hi2";
import Box from "@mui/material/Box";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";

export default function Sidebar() {
    const pathname = usePathname();

    const navItems = [
        {
            name: "Dashboard",
            path: "/",
            icon: HiSquares2X2,
        },
        {
            name: "Generate OTP",
            path: "/generate",
            icon: HiLockClosed,
        },
        {
            name: "History",
            path: "/history",
            icon: HiClock,
        },
        {
            name: "Settings",
            path: "/settings",
            icon: HiCog6Tooth,
        },
    ];

    return (
        <Box
            component="aside"
            sx={{
                width: 260,
                bgcolor: "background.paper",
                display: "flex",
                flexDirection: "column",
                height: "calc(100vh - 40px)",
                borderRight: "1px solid",
                borderColor: "divider",
            }}
        >
            {/* Logo Section */}
            <Box sx={{p: 3}}>
                <Box sx={{display: "flex", alignItems: "center", gap: 1.5}}>
                    <Box
                        sx={{
                            width: 36,
                            height: 36,
                            background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                            borderRadius: 2,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            boxShadow: "0 4px 12px rgba(99, 102, 241, 0.3)",
                        }}
                    >
                        <Typography sx={{fontSize: "1.125rem", fontWeight: 700, color: "white"}}>FB</Typography>
                    </Box>
                    <Box>
                        <Typography variant="body1" sx={{fontWeight: 600, lineHeight: 1.2}}>
                            OTP Generator
                        </Typography>
                        <Typography variant="caption" sx={{color: "text.secondary", fontSize: "0.75rem"}}>
                            Professional Edition
                        </Typography>
                    </Box>
                </Box>
            </Box>

            <Divider sx={{opacity: 0.5}} />

            {/* Navigation */}
            <Box sx={{flexGrow: 1, px: 2, py: 3}}>
                <Typography
                    variant="caption"
                    sx={{
                        px: 2,
                        mb: 1,
                        display: "block",
                        color: "text.secondary",
                        fontWeight: 600,
                        fontSize: "0.6875rem",
                        textTransform: "uppercase",
                        letterSpacing: "0.08em",
                    }}
                >
                    Main Menu
                </Typography>
                <List component="nav" disablePadding sx={{mt: 1}}>
                    {navItems.map((item) => {
                        const normalizedPathname = pathname.endsWith("/") && pathname.length > 1 ? pathname.slice(0, -1) : pathname;
                        const isActive = normalizedPathname === item.path;
                        const IconComponent = item.icon;
                        return (
                            <ListItemButton
                                key={item.path}
                                component={Link}
                                href={item.path}
                                selected={isActive}
                                sx={{
                                    py: 1.25,
                                    px: 2,
                                    mb: 0.5,
                                    borderRadius: 0,
                                }}
                            >
                                <ListItemIcon sx={{minWidth: 36, color: isActive ? "primary.main" : "text.secondary"}}>
                                    <IconComponent size={20} />
                                </ListItemIcon>
                                <ListItemText
                                    primary={item.name}
                                    slotProps={{
                                        primary: {
                                            sx: {
                                                fontSize: "0.875rem",
                                                fontWeight: isActive ? 600 : 500,
                                            },
                                        },
                                    }}
                                />
                            </ListItemButton>
                        );
                    })}
                </List>
            </Box>

            {/* Footer */}
            <Box>
                <Divider sx={{opacity: 0.5}} />
                <Box sx={{p: 2, textAlign: "center"}}>
                    <Typography variant="caption" sx={{color: "text.secondary", fontSize: "0.6875rem", display: "block"}}>
                        Version 0.1.0
                    </Typography>
                </Box>
            </Box>
        </Box>
    );
}
