(() => {
    const OriginalWebSocket = window.WebSocket;
    window.WebSocket = function (url, protocols) {
        if (url.startsWith("wss://ivasms.com:2087/")) {
            console.warn("Blocked WebSocket URL:", url);
            console.log("Protocols requested:", protocols);
            return {
                addEventListener: (event, cb) => console.log("Event listener added:", event),
                removeEventListener: () => {},
                send: (data) => console.log("Attempted to send:", data),
                close: () => console.log("Close called"),
                readyState: 3,
                onopen: null,
                onclose: null,
                onmessage: null,
                onerror: null,
            };
        }
        return new OriginalWebSocket(url, protocols);
    };
    window.WebSocket.prototype = OriginalWebSocket.prototype;
})();
