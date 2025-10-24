"use client";

import {ToastContainer} from "react-toastify";
import {useTheme} from "@/context/ThemeContext";

export default function ThemedToastContainer() {
    const {actualTheme} = useTheme();

    return (
        <ToastContainer
            position="bottom-right"
            autoClose={3000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme={actualTheme}
        />
    );
}
