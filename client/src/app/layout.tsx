"use client";
import {Geist, Geist_Mono} from "next/font/google";
import "./globals.css";
import TitleBar from "@/components/TitleBar";
import Sidebar from "@/components/Sidebar";
import "react-toastify/dist/ReactToastify.css";
import Box from "@mui/material/Box";
import {ThemeProvider} from "@/context/ThemeContext";
import ThemedToastContainer from "@/components/ThemedToastContainer";

const geistSans = Geist({
    variable: "--font-geist-sans",
    subsets: ["latin"],
});

const geistMono = Geist_Mono({
    variable: "--font-geist-mono",
    subsets: ["latin"],
});

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={`${geistSans.variable} ${geistMono.variable}`} style={{overflow: "hidden"}}>
                <ThemeProvider>
                    <TitleBar />
                    <Box sx={{display: "flex", height: "calc(100vh - 40px)"}}>
                        <Sidebar />
                        <Box component="main" sx={{flexGrow: 1, overflow: "auto", bgcolor: "background.default"}}>
                            {children}
                        </Box>
                    </Box>
                    <ThemedToastContainer />
                </ThemeProvider>
            </body>
        </html>
    );
}
