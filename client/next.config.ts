import type {NextConfig} from "next";

const nextConfig: NextConfig = {
    output: "export",
    images: {
        unoptimized: true,
    },
    // Disable server-side features for static export
    trailingSlash: true,
    // Use empty string for relative paths in Electron
    assetPrefix: "",
};

export default nextConfig;
