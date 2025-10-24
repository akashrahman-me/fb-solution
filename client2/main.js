// main.js
const {app, BrowserWindow, ipcMain} = require("electron");
const path = require("path");

const isDev = process.env.NODE_ENV !== "production";

async function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        frame: false, // Remove default titlebar
        titleBarStyle: "hidden",
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, "preload.js"),
        },
    });

    if (isDev) {

        await win.loadURL("http://localhost:3000");
        win.webContents.openDevTools();
    } else {
        // serve exported static files from out/
        const loadURL = require("electron-serve")({directory: "out"});
        await loadURL(win);
    }
}

// Window Controls IPC Handlers
ipcMain.on("window-minimize", (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    win?.minimize();
});

ipcMain.on("window-maximize", (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win?.isMaximized()) {
        win.unmaximize();
    } else {
        win?.maximize();
    }
});

ipcMain.on("window-close", (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    win?.close();
});

// IPC Handlers - Example communication between renderer and main process
ipcMain.on("toMain", (event, data) => {
    console.log("Received from renderer:", data);
    // Send response back
    event.reply("fromMain", {message: "Message received!", echo: data});
});

ipcMain.handle("get-app-path", async () => {
    return app.getPath("userData");
});

app.whenReady().then(createWindow);
app.on("window-all-closed", () => {
    if (process.platform !== "darwin") app.quit();
});
