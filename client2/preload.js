// preload.js
const {contextBridge, ipcRenderer} = require("electron");

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld("electron", {
    // System info
    platform: process.platform,

    // Window controls
    windowMinimize: () => ipcRenderer.send("window-minimize"),
    windowMaximize: () => ipcRenderer.send("window-maximize"),
    windowClose: () => ipcRenderer.send("window-close"),

    // IPC Communication - send messages to main process
    send: (channel, data) => {
        // Whitelist channels for security
        const validChannels = ["toMain", "request-data", "save-data"];
        if (validChannels.includes(channel)) {
            ipcRenderer.send(channel, data);
        }
    },

    // IPC Communication - receive messages from main process
    receive: (channel, func) => {
        const validChannels = ["fromMain", "data-response"];
        if (validChannels.includes(channel)) {
            // Strip event as it includes `sender`
            ipcRenderer.on(channel, (event, ...args) => func(...args));
        }
    },

    // IPC Communication - invoke (request-response pattern)
    invoke: async (channel, data) => {
        const validChannels = ["get-app-path", "read-file", "write-file"];
        if (validChannels.includes(channel)) {
            return await ipcRenderer.invoke(channel, data);
        }
    },

    // App version (if you want to display it)
    getVersion: () => process.env.npm_package_version || "1.0.0",
});

// Optional: Expose Node.js path module for file operations
contextBridge.exposeInMainWorld("path", {
    join: (...args) => require("path").join(...args),
    basename: (path) => require("path").basename(path),
    dirname: (path) => require("path").dirname(path),
});
