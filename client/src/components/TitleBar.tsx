"use client";
import React from "react";
import {HiMinus, HiSquare2Stack, HiXMark} from "react-icons/hi2";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";

export default function TitleBar() {
    const handleMinimize = () => {
        if (window.electron) {
            window.electron.windowMinimize();
        }
    };

    const handleMaximize = () => {
        if (window.electron) {
            window.electron.windowMaximize();
        }
    };

    const handleClose = () => {
        if (window.electron) {
            window.electron.windowClose();
        }
    };

    return (
        <Box
            className="titlebar"
            sx={{
                height: 40,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                px: 2,
                bgcolor: "background.paper",
                borderBottom: "1px solid",
                borderColor: "divider",
            }}
        >
            {/* App Title */}
            <Typography variant="body2" sx={{fontWeight: 600, color: "text.primary", fontSize: "0.8125rem"}}>
                FB OTP Generator
            </Typography>

            {/* Window Controls */}
            <Box sx={{display: "flex", gap: 0.5}}>
                <IconButton onClick={handleMinimize} size="small" sx={{width: 32, height: 32}}>
                    <HiMinus size={14} />
                </IconButton>

                <IconButton onClick={handleMaximize} size="small" sx={{width: 32, height: 32}}>
                    <HiSquare2Stack size={14} />
                </IconButton>

                <IconButton
                    onClick={handleClose}
                    size="small"
                    sx={{
                        width: 32,
                        height: 32,
                        "&:hover": {
                            bgcolor: "error.main",
                            color: "white",
                        },
                    }}
                >
                    <HiXMark size={14} />
                </IconButton>
            </Box>
        </Box>
    );
}
