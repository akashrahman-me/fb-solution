// scripts/copy-backend.js
const fs = require("fs");
const path = require("path");

const backendSrc = path.join(__dirname, "../../fbpanel/dist/fb-backend.exe");
const backendDest = path.join(__dirname, "../backend");

// Create backend directory if it doesn't exist
if (!fs.existsSync(backendDest)) {
    fs.mkdirSync(backendDest, {recursive: true});
}

// Copy backend executable
if (fs.existsSync(backendSrc)) {
    console.log("📦 Copying backend executable...");
    fs.copyFileSync(backendSrc, path.join(backendDest, "fb-backend.exe"));
    console.log("✅ Backend copied successfully!");
} else {
    console.error('❌ Backend executable not found! Run "npm run build:backend" first.');
    process.exit(1);
}
