"use client";
import React, {useState} from "react";
import {toast} from "react-toastify";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import ControlBar from "./components/ControlBar";
import PhoneNumberInput from "./components/PhoneNumberInput";
import ResultsPanel from "./components/ResultsPanel";
import {useJobManager} from "./hooks/useJobManager";
import {parsePhoneNumbers, countValidPhones} from "./utils/phoneUtils";
import {useLocalStorage} from "@/hooks/useLocalStorage";
import {ProxyConfig} from "@/types/api";

export default function GeneratePage() {
    const [phoneNumbers, setPhoneNumbers] = useState("");
    const [concurrency, setConcurrency] = useLocalStorage("fb-checker-concurrency", 5);
    const [headless, setHeadless] = useLocalStorage("fb-checker-headless", true);

    const {results, logs, isRunning, progress, startJob, stopCurrentJob, clearResults} = useJobManager();

    const phoneCount = countValidPhones(phoneNumbers);

    const handleStart = () => {
        const phones = parsePhoneNumbers(phoneNumbers);

        // Load proxy config from localStorage
        const proxyConfigStr = localStorage.getItem("fb-checker-proxy-config");
        let proxyConfig: ProxyConfig | undefined = undefined;

        if (proxyConfigStr) {
            try {
                proxyConfig = JSON.parse(proxyConfigStr);
            } catch (error) {
                console.error("Failed to parse proxy config:", error);
            }
        }

        // Load license key from localStorage
        const licenseKey = localStorage.getItem("fb-checker-license-key");

        startJob(phones, concurrency, headless, proxyConfig, licenseKey || undefined);
    };

    const handleClear = () => {
        clearResults();
        setPhoneNumbers("");
        toast.info("Cleared all data");
    };

    return (
        <Box sx={{height: "100%", display: "flex", flexDirection: "column", overflow: "hidden"}}>
            {/* Header */}
            <Box sx={{px: 6, pt: 5, pb: 3}}>
                <Typography variant="h4" sx={{fontWeight: 700, mb: 1, letterSpacing: "-0.02em"}}>
                    Phone Checker
                </Typography>
                <Typography variant="body2" sx={{color: "text.secondary"}}>
                    Check if phone numbers are registered on Facebook with advanced concurrency control
                </Typography>
            </Box>

            {/* Control Bar */}
            <ControlBar
                concurrency={concurrency}
                setConcurrency={setConcurrency}
                headless={headless}
                setHeadless={setHeadless}
                phoneCount={phoneCount}
                isRunning={isRunning}
                onStart={handleStart}
                onStop={stopCurrentJob}
                onClear={handleClear}
            />

            {/* Main Content - Two Panels */}
            <Box sx={{px: 6, pb: 6, flexGrow: 1, display: "flex", gap: 3, overflow: "hidden"}}>
                <PhoneNumberInput phoneNumbers={phoneNumbers} setPhoneNumbers={setPhoneNumbers} />
                <ResultsPanel results={results} logs={logs} isRunning={isRunning} progress={progress} />
            </Box>
        </Box>
    );
}
