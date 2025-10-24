"use client";
import React from "react";
import Link from "next/link";
import {HiLockClosed, HiClock, HiChartBar, HiCog6Tooth} from "react-icons/hi2";
import SimpleBar from "simplebar-react";
import "simplebar-react/dist/simplebar.min.css";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Button from "@mui/material/Button";
import {useTheme} from "@mui/material/styles";

function Home() {
    const theme = useTheme();

    const features = [
        {
            icon: HiLockClosed,
            title: "Secure Checking",
            description: "Check phone numbers with advanced security features and privacy protection",
            color: theme.palette.primary.main,
        },
        {
            icon: HiClock,
            title: "Track History",
            description: "Keep track of all your checked numbers with detailed logs and results",
            color: theme.palette.secondary.main,
        },
        {
            icon: HiChartBar,
            title: "Analytics",
            description: "Monitor your checking patterns and view comprehensive statistics",
            color: theme.palette.success.main,
        },
        {
            icon: HiCog6Tooth,
            title: "Customizable",
            description: "Configure proxy settings, concurrency, and other preferences",
            color: theme.palette.warning.main,
        },
    ];

    return (
        <Box sx={{height: "100%", display: "flex", flexDirection: "column", overflow: "hidden"}}>
            <SimpleBar style={{maxHeight: "100%", height: "100%"}}>
                {/* Hero Section */}
                <Box sx={{px: 6, pt: 6, pb: 4}}>
                    <Typography
                        variant="caption"
                        sx={{
                            color: "primary.main",
                            fontWeight: 600,
                            fontSize: "0.75rem",
                            textTransform: "uppercase",
                            letterSpacing: "0.1em",
                            mb: 2,
                            display: "block",
                        }}
                    >
                        Professional OTP Solution
                    </Typography>
                    <Typography variant="h3" sx={{fontWeight: 700, mb: 2, letterSpacing: "-0.02em"}}>
                        Welcome to FB Phone Checker
                    </Typography>
                    <Typography variant="body1" sx={{color: "text.secondary", mb: 4, maxWidth: 600, lineHeight: 1.7}}>
                        Efficiently check if phone numbers are registered on Facebook with a professional-grade desktop application.
                        Designed for efficiency and security.
                    </Typography>
                    <Box sx={{display: "flex", gap: 2}}>
                        <Button variant="contained" size="large" component={Link} href="/generate" sx={{px: 4}}>
                            Start Checking
                        </Button>
                        <Button variant="outlined" size="large" component={Link} href="/jobs" sx={{px: 4}}>
                            View Jobs
                        </Button>
                    </Box>
                </Box>

                {/* Features Grid */}
                <Box sx={{px: 6, pb: 6, flexGrow: 1}}>
                    <Typography variant="h6" sx={{fontWeight: 600, mb: 3, fontSize: "0.9375rem"}}>
                        Key Features
                    </Typography>
                    <Box sx={{display: "grid", gridTemplateColumns: {xs: "1fr", md: "repeat(2, 1fr)"}, gap: 2.5}}>
                        {features.map((feature) => {
                            const IconComponent = feature.icon;
                            return (
                                <Card
                                    key={feature.title}
                                    sx={{
                                        height: "100%",
                                        transition: "all 0.3s ease",
                                        "&:hover": {
                                            transform: "translateY(-2px)",
                                        },
                                    }}
                                >
                                    <CardContent sx={{p: 3}}>
                                        <Box
                                            sx={{
                                                width: 48,
                                                height: 48,
                                                background: `linear-gradient(135deg, ${feature.color}40 0%, ${feature.color}20 100%)`,
                                                borderRadius: 2,
                                                display: "flex",
                                                alignItems: "center",
                                                justifyContent: "center",
                                                mb: 2,
                                                border: `1px solid ${feature.color}30`,
                                            }}
                                        >
                                            <IconComponent size={24} style={{color: feature.color}} />
                                        </Box>
                                        <Typography variant="h6" sx={{fontWeight: 600, mb: 1, fontSize: "1rem"}}>
                                            {feature.title}
                                        </Typography>
                                        <Typography variant="body2" sx={{color: "text.secondary", lineHeight: 1.6}}>
                                            {feature.description}
                                        </Typography>
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </Box>
                </Box>
            </SimpleBar>
        </Box>
    );
}

export default Home;
