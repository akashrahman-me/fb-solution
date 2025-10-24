import React from "react";
import {HiPlay, HiStop, HiArrowPath} from "react-icons/hi2";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
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
                    gap: 2,
                    p: 2,
                    bgcolor: "background.paper",
                    borderRadius: 2,
                    border: "1px solid",
                    borderColor: "divider",
                    flexWrap: "wrap",
                }}
            >
                {/* Concurrency Control */}
                <Box sx={{display: "flex", alignItems: "center", gap: 1}}>
                    <Typography
                        variant="body2"
                        sx={{color: "text.secondary", fontSize: "0.8125rem", fontWeight: 500, whiteSpace: "nowrap"}}
                    >
                        Concurrency:
                    </Typography>
                    <Select
                        value={concurrency}
                        onChange={(e) => setConcurrency(Number(e.target.value))}
                        size="small"
                        sx={{
                            width: 70,
                            fontSize: "0.875rem",
                            "& .MuiSelect-select": {
                                textAlign: "center",
                                fontWeight: 600,
                                padding: "6px 8px",
                            },
                        }}
                    >
                        <MenuItem value={1}>1</MenuItem>
                        <MenuItem value={2}>2</MenuItem>
                        <MenuItem value={5}>5</MenuItem>
                        <MenuItem value={10}>10</MenuItem>
                        <MenuItem value={20}>20</MenuItem>
                        <MenuItem value={50}>50</MenuItem>
                        <MenuItem value={100}>100</MenuItem>
                    </Select>
                </Box>

                <Divider orientation="vertical" flexItem sx={{opacity: 0.5, mx: 0.5}} />

                {/* Headless Mode Toggle */}
                <FormControlLabel
                    control={
                        <Switch checked={headless} onChange={(e) => setHeadless(e.target.checked)} disabled={isRunning} size="small" />
                    }
                    label={
                        <Typography
                            variant="body2"
                            sx={{color: "text.secondary", fontSize: "0.8125rem", fontWeight: 500, whiteSpace: "nowrap"}}
                        >
                            &nbsp;&nbsp;Headless
                        </Typography>
                    }
                    sx={{margin: 0, mr: 1}}
                />

                <Divider orientation="vertical" flexItem sx={{opacity: 0.5, mx: 0.5}} />

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
                    <Typography variant="body2" sx={{color: "text.secondary", fontSize: "0.8125rem", whiteSpace: "nowrap"}}>
                        <Typography component="span" sx={{fontWeight: 600, color: "text.primary"}}>
                            {phoneCount}
                        </Typography>{" "}
                        loaded
                    </Typography>
                </Box>

                {/* Action Buttons */}
                <Box sx={{display: "flex", gap: 1.5, ml: "auto"}}>
                    <Button onClick={onClear} disabled={isRunning} variant="outlined" size="small" startIcon={<HiArrowPath size={16} />}>
                        Clear
                    </Button>
                    {isRunning ? (
                        <Button onClick={onStop} variant="contained" color="error" size="small" startIcon={<HiStop size={16} />}>
                            Stop
                        </Button>
                    ) : (
                        <Button
                            onClick={onStart}
                            disabled={phoneCount === 0}
                            variant="contained"
                            size="small"
                            startIcon={<HiPlay size={16} />}
                        >
                            Start
                        </Button>
                    )}
                </Box>
            </Box>
        </Box>
    );
}
