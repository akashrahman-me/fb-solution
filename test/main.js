const WebSocket = require("ws");

const websocketURL = `
wss://ivasms.com:2087/socket.io/?token=eyJpdiI6ImFDZXZFeXhzQXpybEFlUUkzQlFBV1E9PSIsInZhbHVlIjoiZTV1ZDNzMm93bEZlZ1o4NVdHb3g0RlVVZkx4d3dVQVVUOVFuL0xjdnk3Q3lFcnBLOUZsVVhHb1M2TGNTa0RuZ0pJZ3BPVmw5T3ZKd1E3OXUyNFYxMXFMK2FxRjNiaTFxZENjYjJEd3QwNFFvazUraFRNMUxLNVlueXNNYzYzU292TmkxN0ZRNXdwNUZ6M1Z0NkxGdjNJRkNsQ25ic05hcEVjMlc0M0VMajB6QkxLeEdpQ2V1QkFyalAwVkUyc3hJdVlHMGthaTAxakcyNzZpWS8rZFhCb2V3VzdGdDZzbnZSN3poaTgzSGtKYW50QVBaY1hWbGRGMTFCVGFDL0Q1ejhkL1RvQWhjTzY5TVkyWkdWTVNvbG5VMHY1bldvYlpiK1hmbGpyS01nZVlybzZyalFrdlN5ZXJoOXFIYjM4ZGlMUzZ3TmcwN0RYR2w2Q2hPbndlTUlnbExoTlI1UjAwQTNENWhYWEZIV1RCNHo4MzFlcEdVemNkWkRwOEJIVW5sOFJIajlTNXRWVCttNmxyb3NTekdnNVFZa2ZialhRS05HdGRleVpoVEtHNHNGR29JdTh5b0U5QVBJdzlLYnRLRHRpS1lRdXU0R01Oa3FORnM0SFhhczFwSnFhc1R6NDFyRkUvaU5PV1dpN0VlQjJqU3NmVFV4ZjJDTll1Mml2aU9peHhzOWV2dWRIaDg0N0tmQ2w4VWErYUtDUnhHZWNyZWRLS3BQR0dnRWkwPSIsIm1hYyI6ImZhNDk3MTAxZmY1ZjgwY2RmY2FjYmIyOGJkYWE3NTE4YjNlYmZhOWY3MzMwMzlhM2Y4ZGZmZTRiMTdiNTE1NDIiLCJ0YWciOiIifQ%3D%3D&user=cb753baf60db1effea276ebdb35168a5&EIO=4&transport=websocket`;

console.log("🔌 Connecting to WebSocket...");

// Create WebSocket connection with headers
const ws = new WebSocket(websocketURL, {
    headers: {
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        origin: "https://www.ivasms.com",
        pragma: "no-cache",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    },
});

// Connection opened
ws.on("open", () => {
    console.log("✅ WebSocket Connected!");
});

// Listen for messages
ws.on("message", (data) => {
    console.log("\n📩 Message received:");
    console.log("Raw data:", data.toString());

    // Try to parse as JSON if possible
    try {
        const parsed = JSON.parse(data.toString());
        console.log("📦 Parsed data:", JSON.stringify(parsed, null, 2));
    } catch (e) {
        console.log("📝 Data is not JSON format");
    }
});

// Connection closed
ws.on("close", (code, reason) => {
    console.log("\n❌ WebSocket Closed");
    console.log("Close code:", code);
    console.log("Close reason:", reason.toString());
});

// Connection error
ws.on("error", (error) => {
    console.error("\n⚠️ WebSocket Error:", error.message);
});

// Handle process termination
process.on("SIGINT", () => {
    console.log("\n\n🛑 Closing WebSocket connection...");
    ws.close();
    process.exit(0);
});
