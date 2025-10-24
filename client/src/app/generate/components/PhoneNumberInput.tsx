import React from "react";
import {HiSparkles, HiXMark} from "react-icons/hi2";
import {toast} from "react-toastify";
import SimpleBar from "simplebar-react";
import "simplebar-react/dist/simplebar.min.css";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Card from "@mui/material/Card";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import {cleanPhoneNumbers, removeDuplicatePhones, countValidPhones} from "../utils/phoneUtils";

interface PhoneNumberInputProps {
    phoneNumbers: string;
    setPhoneNumbers: (value: string) => void;
}

export default function PhoneNumberInput({phoneNumbers, setPhoneNumbers}: PhoneNumberInputProps) {
    const phoneCount = countValidPhones(phoneNumbers);
    const totalLines = phoneNumbers.split("\n").length;

    const handleCleanUp = () => {
        const cleaned = cleanPhoneNumbers(phoneNumbers);
        setPhoneNumbers(cleaned);
        toast.success("Removed empty lines");
    };

    const handleRemoveDuplicates = () => {
        const {cleaned, removedCount} = removeDuplicatePhones(phoneNumbers);
        setPhoneNumbers(cleaned);
        toast.success(`Removed ${removedCount} duplicates`);
    };

    return (
        <Card sx={{flex: 1, display: "flex", flexDirection: "column", overflow: "hidden"}}>
            {/* Header */}
            <Box sx={{p: 3, borderBottom: "1px solid", borderColor: "divider"}}>
                <Typography variant="h6" sx={{fontWeight: 600, mb: 0.5, fontSize: "1rem"}}>
                    Phone Numbers
                </Typography>
                <Typography variant="caption" sx={{color: "text.secondary", fontSize: "0.75rem"}}>
                    Enter one phone number per line
                </Typography>
            </Box>

            {/* Input Area */}
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

            {/* Stats & Quick Actions */}
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
                            {totalLines}
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
                            {totalLines - phoneCount}
                        </Typography>
                    </Box>
                </Box>
                <Box sx={{display: "flex", gap: 0.5}}>
                    <Tooltip title="Clean Up - Remove empty lines" arrow placement="top">
                        <span>
                            <IconButton
                                onClick={handleCleanUp}
                                disabled={totalLines === phoneCount}
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
                            onClick={handleRemoveDuplicates}
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
    );
}
