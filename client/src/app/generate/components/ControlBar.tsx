import React from "react";
import {HiPlay, HiStop, HiArrowPath} from "react-icons/hi2";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import Switch from "@mui/material/Switch";
import FormControlLabel from "@mui/material/FormControlLabel";

interface ControlBarProps {
    concurrency: number;
    setConcurrency: (value: number) => void;
    headless: boolean;
    setHeadless: (value: boolean) => void;
    phoneCount: number;
    isRunning: boolean;
    onStart: () => void;
    onStop: () => void;
    onClear: () => void;
}

export default function ControlBar({
    concurrency,
    setConcurrency,
    headless,
    setHeadless,
    phoneCount,
    isRunning,
    onStart,
    onStop,
    onClear,
}: ControlBarProps) {
    return (
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
                {/* Concurrency Control */}
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

                {/* Headless Mode Toggle */}
                <Box sx={{display: "flex", alignItems: "center", gap: 1}}>
                    <FormControlLabel
                        control={
                            <Switch checked={headless} onChange={(e) => setHeadless(e.target.checked)} disabled={isRunning} size="small" />
                        }
                        label={
                            <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem", fontWeight: 500}}>
                                Headless Mode
                            </Typography>
                        }
                        sx={{margin: 0}}
                    />
                </Box>

                <Divider orientation="vertical" flexItem sx={{opacity: 0.5}} />

                {/* Phone Count Indicator */}
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

                {/* Action Buttons */}
                <Box sx={{display: "flex", gap: 1.5, ml: "auto"}}>
                    <Button onClick={onClear} disabled={isRunning} variant="outlined" size="medium" startIcon={<HiArrowPath size={16} />}>
                        Clear
                    </Button>
                    {isRunning ? (
                        <Button onClick={onStop} variant="contained" color="error" size="medium" startIcon={<HiStop size={16} />}>
                            Stop
                        </Button>
                    ) : (
                        <Button
                            onClick={onStart}
                            disabled={phoneCount === 0}
                            variant="contained"
                            size="medium"
                            startIcon={<HiPlay size={16} />}
                        >
                            Start Checking
                        </Button>
                    )}
                </Box>
            </Box>
        </Box>
    );
}
