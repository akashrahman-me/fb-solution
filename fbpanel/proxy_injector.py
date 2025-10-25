#!/usr/bin/env python3
"""
Simple HTTP proxy that forwards requests to an upstream authenticated proxy.
"""
import socket
import select
import threading
import base64
import re
from urllib.parse import urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime
from collections import deque
import logging

# Setup logging for proxy
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - PROXY - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# --- Configuration ---
LOCAL_PROXY_HOST = "127.0.0.1"
LOCAL_PROXY_PORT = 8080
STATS_SERVER_PORT = 8081

# Bandwidth limit: abort requests if response exceeds this size
MAX_RESPONSE_SIZE = 128 * 1024 * 1024

# Datacenter Proxy Credentials - Now configurable at runtime
# ---------------------
REMOTE_SERVER = None
REMOTE_PORT = None
REMOTE_USERNAME = None
REMOTE_PASSWORD = None
PROXY_AUTH = None
USE_PROXY = False

def configure_proxy(server=None, port=None, username=None, password=None, enabled=True):
    """
    Configure proxy settings at runtime

    Args:
        server: Proxy server address (e.g., "31.59.20.176")
        port: Proxy server port (e.g., 6754)
        username: Proxy username
        password: Proxy password
        enabled: Whether to use proxy or connect directly
    """
    global REMOTE_SERVER, REMOTE_PORT, REMOTE_USERNAME, REMOTE_PASSWORD, PROXY_AUTH, USE_PROXY

    logger.info(f"🔧 Configuring proxy: enabled={enabled}, server={server}, port={port}")
    
    USE_PROXY = enabled

    if enabled and server and port:
        REMOTE_SERVER = server
        REMOTE_PORT = int(port)
        REMOTE_USERNAME = username
        REMOTE_PASSWORD = password

        if username and password:
            PROXY_AUTH = base64.b64encode(f"{username}:{password}".encode()).decode()
        else:
            PROXY_AUTH = None

        print(f"✓ Proxy configured: {REMOTE_SERVER}:{REMOTE_PORT} (Auth: {'Yes' if PROXY_AUTH else 'No'})")
    else:
        REMOTE_SERVER = None
        REMOTE_PORT = None
        REMOTE_USERNAME = None
        REMOTE_PASSWORD = None
        PROXY_AUTH = None
        print("✓ Direct connection mode (no proxy)")

# Global statistics
class ProxyStats:
    def __init__(self):
        self.total_sent = 0
        self.total_received = 0
        self.total_requests = 0
        self.start_time = datetime.now()
        self.lock = threading.Lock()
        self.logs = deque(maxlen=100)  # Keep last 100 requests

    def add_request(self, sent, received, url=""):
        with self.lock:
            self.total_sent += sent
            self.total_received += received
            self.total_requests += 1
            # Add log entry
            self.logs.append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'url': url,
                'sent': sent,
                'received': received,
                'total': sent + received
            })

    def get_stats(self):
        with self.lock:
            return {
                'total_sent': self.total_sent,
                'total_received': self.total_received,
                'total_data': self.total_sent + self.total_received,
                'total_requests': self.total_requests,
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
            }

    def get_logs(self):
        with self.lock:
            return list(self.logs)

stats = ProxyStats()

class StatsHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default logging
        pass

    def do_GET(self):
        if self.path == '/stats' or self.path == '/':
            data = stats.get_stats()
            logs = stats.get_logs()

            # Format bytes
            def format_bytes(b):
                if b >= 1024 * 1024 * 1024:
                    return f"{b / (1024 * 1024 * 1024):.2f} GB"
                elif b >= 1024 * 1024:
                    return f"{b / (1024 * 1024):.2f} MB"
                elif b >= 1024:
                    return f"{b / 1024:.1f} KB"
                else:
                    return f"{b} B"

            uptime_minutes = int(data['uptime_seconds'] / 60)
            uptime_hours = int(uptime_minutes / 60)
            uptime_minutes = uptime_minutes % 60

            # Generate log entries HTML
            log_entries = ""
            for log in reversed(logs):  # Show newest first
                log_entries += f"""
                    <div class="log-entry">
                        <span class="log-time">{log['timestamp']}</span>
                        <span class="log-url">🌐 {log['url']}</span>
                        <span class="log-stats">
                            <span class="log-upload">⬆️ {format_bytes(log['sent'])}</span>
                            <span class="log-download">⬇️ {format_bytes(log['received'])}</span>
                            <span class="log-total">✅ {format_bytes(log['total'])}</span>
                        </span>
                    </div>
                """

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Proxy Stats</title>
                <meta charset="utf-8">
                <meta http-equiv="refresh" content="3">
                <style>
                    * {{
                        box-sizing: border-box;
                    }}
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 20px;
                        min-height: 100vh;
                    }}
                    .wrapper {{
                        max-width: 1400px;
                        margin: 0 auto;
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 20px;
                    }}
                    .container {{
                        background: white;
                        border-radius: 15px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        padding: 30px;
                    }}
                    .full-width {{
                        grid-column: 1 / -1;
                    }}
                    h1 {{
                        color: #333;
                        margin-top: 0;
                        text-align: center;
                        font-size: 2em;
                        margin-bottom: 20px;
                    }}
                    h2 {{
                        color: #333;
                        margin-top: 0;
                        font-size: 1.5em;
                        margin-bottom: 15px;
                        border-bottom: 2px solid #667eea;
                        padding-bottom: 10px;
                    }}
                    .stat-box {{
                        background: #f8f9fa;
                        border-left: 4px solid #667eea;
                        padding: 15px 20px;
                        margin: 10px 0;
                        border-radius: 5px;
                    }}
                    .stat-label {{
                        color: #666;
                        font-size: 0.85em;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        margin-bottom: 5px;
                    }}
                    .stat-value {{
                        color: #333;
                        font-size: 1.6em;
                        font-weight: bold;
                    }}
                    .total {{
                        border-left-color: #28a745;
                    }}
                    .upload {{
                        border-left-color: #ffc107;
                    }}
                    .download {{
                        border-left-color: #17a2b8;
                    }}
                    .info {{
                        text-align: center;
                        color: #666;
                        margin-top: 20px;
                        font-size: 0.85em;
                    }}
                    .emoji {{
                        font-size: 1.1em;
                        margin-right: 5px;
                    }}
                    .logs-container {{
                        background: #1e1e1e;
                        border-radius: 8px;
                        padding: 15px;
                        max-height: 600px;
                        overflow-y: auto;
                        font-family: 'Consolas', 'Monaco', monospace;
                    }}
                    .log-entry {{
                        color: #d4d4d4;
                        padding: 8px 10px;
                        margin: 5px 0;
                        background: #2d2d2d;
                        border-radius: 4px;
                        font-size: 0.9em;
                        line-height: 1.6;
                        border-left: 3px solid #667eea;
                        display: flex;
                        flex-direction: column;
                        gap: 5px;
                    }}
                    .log-entry:hover {{
                        background: #3d3d3d;
                    }}
                    .log-time {{
                        color: #858585;
                        font-size: 0.85em;
                        font-weight: bold;
                    }}
                    .log-url {{
                        color: #4ec9b0;
                        word-break: break-all;
                    }}
                    .log-stats {{
                        display: flex;
                        gap: 15px;
                        font-size: 0.9em;
                    }}
                    .log-upload {{
                        color: #ffc107;
                    }}
                    .log-download {{
                        color: #17a2b8;
                    }}
                    .log-total {{
                        color: #28a745;
                    }}
                    .logs-container::-webkit-scrollbar {{
                        width: 8px;
                    }}
                    .logs-container::-webkit-scrollbar-track {{
                        background: #1e1e1e;
                    }}
                    .logs-container::-webkit-scrollbar-thumb {{
                        background: #667eea;
                        border-radius: 4px;
                    }}
                    @media (max-width: 968px) {{
                        .wrapper {{
                            grid-template-columns: 1fr;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="wrapper">
                    <div class="container">
                        <h1>📊 Proxy Statistics</h1>

                        <div class="stat-box total">
                            <div class="stat-label"><span class="emoji">✅</span>Total Data</div>
                            <div class="stat-value">{format_bytes(data['total_data'])}</div>
                        </div>

                        <div class="stat-box upload">
                            <div class="stat-label"><span class="emoji">⬆️</span>Total Uploaded</div>
                            <div class="stat-value">{format_bytes(data['total_sent'])}</div>
                        </div>

                        <div class="stat-box download">
                            <div class="stat-label"><span class="emoji">⬇️</span>Total Downloaded</div>
                            <div class="stat-value">{format_bytes(data['total_received'])}</div>
                        </div>

                        <div class="stat-box">
                            <div class="stat-label"><span class="emoji">🔢</span>Total Requests</div>
                            <div class="stat-value">{data['total_requests']:,}</div>
                        </div>

                        <div class="stat-box">
                            <div class="stat-label"><span class="emoji">⏱️</span>Uptime</div>
                            <div class="stat-value">{uptime_hours}h {uptime_minutes}m</div>
                        </div>

                        <div class="info">
                            Auto-refreshes every 3 seconds
                        </div>
                    </div>

                    <div class="container">
                        <h2>📋 Live Request Logs</h2>
                        <div class="logs-container">
                            {log_entries if log_entries else '<div class="log-entry">No requests yet...</div>'}
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

        elif self.path == '/json':
            data = stats.get_stats()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode())

        elif self.path == '/logs':
            logs = stats.get_logs()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(logs, indent=2).encode())

        else:
            self.send_response(404)
            self.end_headers()

def start_stats_server():
    """Start the stats HTTP server"""
    server = HTTPServer((LOCAL_PROXY_HOST, STATS_SERVER_PORT), StatsHandler)
    print(f"✓ Stats server started on http://{LOCAL_PROXY_HOST}:{STATS_SERVER_PORT}/stats")
    server.serve_forever()

class ProxyThread(threading.Thread):
    def __init__(self, client_socket, client_address):
        threading.Thread.__init__(self)
        self.client = client_socket
        self.client_address = client_address
        self.daemon = True
        self.bytes_sent = 0
        self.bytes_received = 0
        self.url = ""

    def run(self):
        try:
            # Receive the client's request
            request = self.client.recv(4096)
            if not request:
                return

            request_str = request.decode('latin-1', errors='ignore')

            # Extract URL from request
            self.url = self.extract_url(request_str)
            self.bytes_sent += len(request)

            if USE_PROXY and REMOTE_SERVER and REMOTE_PORT:
                # Proxy mode: Forward to upstream proxy
                self.handle_proxy_mode(request, request_str)
            else:
                # Direct mode: Connect directly to target server
                self.handle_direct_mode(request, request_str)
                
        except Exception as e:
            pass
        finally:
            self.client.close()
            self.print_stats()

    def handle_proxy_mode(self, request, request_str):
        """Handle request by forwarding to upstream proxy"""
        try:
            # Add Proxy-Authorization header if not present
            lines = request_str.split('\r\n')
            has_proxy_auth = any('Proxy-Authorization' in line for line in lines)

            if PROXY_AUTH and not has_proxy_auth:
                # Insert Proxy-Authorization after the first line
                lines.insert(1, f'Proxy-Authorization: Basic {PROXY_AUTH}')
                request_str = '\r\n'.join(lines)
                request = request_str.encode('latin-1')

            # Connect to the upstream proxy
            upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            upstream.settimeout(10)
            
            try:
                upstream.connect((REMOTE_SERVER, REMOTE_PORT))

                # Send the modified request to upstream proxy
                upstream.sendall(request)
                
                # Relay data between client and upstream proxy
                self.relay_data(self.client, upstream)

            except socket.timeout:
                self.client.send(b"HTTP/1.1 504 Gateway Timeout\r\n\r\n")
            except ConnectionRefusedError:
                self.client.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            except Exception as e:
                self.client.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            finally:
                upstream.close()
                
        except Exception as e:
            pass

    def handle_direct_mode(self, request, request_str):
        """Handle request by connecting directly to target server"""
        try:
            lines = request_str.split('\r\n')
            if not lines:
                return

            first_line = lines[0]
            parts = first_line.split(' ')
            if len(parts) < 2:
                return

            method = parts[0]
            url = parts[1]

            # Extract target host and port
            target_host = None
            target_port = 80

            if method == 'CONNECT':
                # HTTPS CONNECT request
                if ':' in url:
                    target_host, port_str = url.split(':', 1)
                    target_port = int(port_str)
                else:
                    target_host = url
                    target_port = 443
            else:
                # HTTP request - extract host from headers
                for line in lines[1:]:
                    if line.lower().startswith('host:'):
                        host_value = line.split(':', 1)[1].strip()
                        if ':' in host_value:
                            target_host, port_str = host_value.split(':', 1)
                            target_port = int(port_str)
                        else:
                            target_host = host_value
                            target_port = 80
                        break

            if not target_host:
                self.client.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                return

            # Connect directly to target server
            target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target.settimeout(10)

            try:
                target.connect((target_host, target_port))

                if method == 'CONNECT':
                    # For HTTPS, send connection established and relay
                    self.client.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                    self.relay_data(self.client, target)
                else:
                    # For HTTP, forward the request
                    target.sendall(request)
                    self.relay_data(self.client, target)

            except socket.timeout:
                self.client.send(b"HTTP/1.1 504 Gateway Timeout\r\n\r\n")
            except ConnectionRefusedError:
                self.client.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            except Exception as e:
                self.client.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            finally:
                target.close()

        except Exception as e:
            pass

    def extract_url(self, request_str):
        """Extract URL from HTTP request"""
        try:
            lines = request_str.split('\r\n')
            if lines:
                first_line = lines[0]
                parts = first_line.split(' ')
                if len(parts) >= 2:
                    method = parts[0]
                    url = parts[1]

                    # If it's a CONNECT request (HTTPS), format it
                    if method == 'CONNECT':
                        return f"https://{url}"
                    # If URL is absolute, use it
                    elif url.startswith('http'):
                        return url
                    # Otherwise, try to find Host header
                    else:
                        for line in lines[1:]:
                            if line.lower().startswith('host:'):
                                host = line.split(':', 1)[1].strip()
                                return f"http://{host}{url}"
                        return url
        except:
            pass
        return "unknown"

    def format_bytes(self, bytes_count):
        """Format bytes to appropriate unit (Bytes, KB, or MB)"""
        if bytes_count >= 1024 * 1024:  # >= 1MB
            return f"{bytes_count / (1024 * 1024):.1f}MB"
        elif bytes_count >= 1024:  # >= 1KB
            return f"{bytes_count / 1024:.1f}KB"
        else:  # < 1KB
            return f"{bytes_count}B"

    def print_stats(self):
        """Print transfer statistics"""
        total = self.bytes_sent + self.bytes_received
        if total > 0:
            # Update global stats with URL
            stats.add_request(self.bytes_sent, self.bytes_received, self.url)
            print(f"🌐 {self.url} | ⬆️ {self.format_bytes(self.bytes_sent)} | ⬇️ {self.format_bytes(self.bytes_received)} | ✅ {self.format_bytes(total)}")

    def relay_data(self, client, upstream):
        """Relay data between client and upstream proxy with size limit"""
        try:
            sockets = [client, upstream]
            timeout = 60
            response_size = 0
            size_limit_exceeded = False

            while True:
                readable, _, exceptional = select.select(sockets, [], sockets, timeout)
                
                if exceptional:
                    break
                    
                if not readable:
                    break
                
                for sock in readable:
                    try:
                        data = sock.recv(8192)
                        if not data:
                            return
                        
                        if sock is client:
                            # Data from client to upstream (request)
                            upstream.send(data)
                            self.bytes_sent += len(data)
                        else:
                            # Data from upstream to client (response)
                            response_size += len(data)

                            # Check if response exceeds size limit
                            if response_size > MAX_RESPONSE_SIZE:
                                if not size_limit_exceeded:
                                    size_limit_exceeded = True
                                    print(f"⚠️  {self.url} | Response size exceeded {MAX_RESPONSE_SIZE / 1024}KB limit - Aborting download")
                                # Stop receiving more data from upstream
                                return

                            client.send(data)
                            self.bytes_received += len(data)
                    except:
                        return
                        
        except Exception as e:
            pass


def start_proxy_server(proxy_port=None, stats_port=None):
    """
    Start the local proxy server

    Args:
        proxy_port: Port for proxy server (default: 8080)
        stats_port: Port for stats server (default: 8081)
    """
    global LOCAL_PROXY_PORT, STATS_SERVER_PORT

    # Use custom ports if provided
    if proxy_port is not None:
        LOCAL_PROXY_PORT = proxy_port
    if stats_port is not None:
        STATS_SERVER_PORT = stats_port

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # Try to bind to the port
        server.bind((LOCAL_PROXY_HOST, LOCAL_PROXY_PORT))
        server.listen(100)

        logger.info(f"✓ Proxy server started on {LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}")
        if USE_PROXY and REMOTE_SERVER:
            logger.info(f"✓ Forwarding to: {REMOTE_SERVER}:{REMOTE_PORT}")
        else:
            logger.info(f"✓ Direct connection mode (no upstream proxy)")

        # Start stats server in a separate thread with error handling
        try:
            stats_thread = threading.Thread(target=start_stats_server, daemon=True)
            stats_thread.start()
            logger.info(f"✓ Stats server starting on {LOCAL_PROXY_HOST}:{STATS_SERVER_PORT}")
        except Exception as e:
            logger.warning(f"⚠ Warning: Stats server failed to start: {e}")

        logger.info(f"✓ Proxy ready for connections\n")

        while True:
            client_socket, client_address = server.accept()
            proxy_thread = ProxyThread(client_socket, client_address)
            proxy_thread.start()

    except KeyboardInterrupt:
        logger.info("\n\nShutting down proxy server...")
    except OSError as e:
        if e.errno == 10048:  # Windows: Address already in use
            logger.error(f"❌ Port {LOCAL_PROXY_PORT} is already in use!")
            logger.error(f"   Please close any application using port {LOCAL_PROXY_PORT} or use a different port.")
        elif e.errno == 98:  # Linux: Address already in use
            logger.error(f"❌ Port {LOCAL_PROXY_PORT} is already in use!")
            logger.error(f"   Please close any application using port {LOCAL_PROXY_PORT} or use a different port.")
        else:
            logger.error(f"❌ Network error: {e}")
    except Exception as e:
        logger.error(f"❌ Error starting proxy server: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        try:
            server.close()
        except:
            pass
        logger.info("Proxy server stopped.")


def open_proxy_settings_dialog():
    """Open a settings dialog to configure proxy settings"""
    try:
        import customtkinter as ctk
    except ImportError:
        print("CustomTkinter not available, cannot open settings dialog")
        return

    # Create dialog window
    dialog = ctk.CTkToplevel()
    dialog.title("Proxy Settings")
    dialog.geometry("600x520")
    dialog.resizable(False, False)

    # Make dialog modal
    dialog.grab_set()
    dialog.focus_set()

    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
    y = (dialog.winfo_screenheight() // 2) - (520 // 2)
    dialog.geometry(f"600x520+{x}+{y}")

    # Main container
    main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    main_frame.pack(fill="both", expand=True, padx=30, pady=30)

    # Title
    title_label = ctk.CTkLabel(
        main_frame,
        text="🌐 Proxy Configuration",
        font=ctk.CTkFont(size=24, weight="bold")
    )
    title_label.pack(pady=(0, 10))

    subtitle_label = ctk.CTkLabel(
        main_frame,
        text="Configure your proxy server settings",
        font=ctk.CTkFont(size=12),
        text_color="gray"
    )
    subtitle_label.pack(pady=(0, 25))

    # Enable/Disable Proxy
    proxy_enabled_var = ctk.BooleanVar(value=USE_PROXY)

    enable_frame = ctk.CTkFrame(main_frame, fg_color=("#e2e8f0", "#1e293b"), corner_radius=10)
    enable_frame.pack(fill="x", pady=(0, 20))

    enable_inner = ctk.CTkFrame(enable_frame, fg_color="transparent")
    enable_inner.pack(fill="x", padx=20, pady=15)

    enable_label = ctk.CTkLabel(
        enable_inner,
        text="Enable Proxy",
        font=ctk.CTkFont(size=14, weight="bold")
    )
    enable_label.pack(side="left")

    enable_switch = ctk.CTkSwitch(
        enable_inner,
        text="",
        variable=proxy_enabled_var,
        width=50
    )
    enable_switch.pack(side="right")

    # Proxy Settings Form
    form_frame = ctk.CTkFrame(main_frame, fg_color=("#f8fafc", "#0f172a"), corner_radius=10)
    form_frame.pack(fill="both", expand=True, pady=(0, 20))

    form_inner = ctk.CTkFrame(form_frame, fg_color="transparent")
    form_inner.pack(fill="both", expand=True, padx=25, pady=25)

    # Server Address
    server_label = ctk.CTkLabel(
        form_inner,
        text="Proxy Server Address:",
        font=ctk.CTkFont(size=13, weight="bold"),
        anchor="w"
    )
    server_label.pack(fill="x", pady=(0, 5))

    server_entry = ctk.CTkEntry(
        form_inner,
        placeholder_text="e.g., 31.59.20.176",
        height=40,
        font=ctk.CTkFont(size=13)
    )
    server_entry.pack(fill="x", pady=(0, 15))
    if REMOTE_SERVER:
        server_entry.insert(0, REMOTE_SERVER)

    # Port
    port_label = ctk.CTkLabel(
        form_inner,
        text="Proxy Port:",
        font=ctk.CTkFont(size=13, weight="bold"),
        anchor="w"
    )
    port_label.pack(fill="x", pady=(0, 5))

    port_entry = ctk.CTkEntry(
        form_inner,
        placeholder_text="e.g., 6754",
        height=40,
        font=ctk.CTkFont(size=13)
    )
    port_entry.pack(fill="x", pady=(0, 15))
    if REMOTE_PORT:
        port_entry.insert(0, str(REMOTE_PORT))

    # Username
    username_label = ctk.CTkLabel(
        form_inner,
        text="Username (Optional):",
        font=ctk.CTkFont(size=13, weight="bold"),
        anchor="w"
    )
    username_label.pack(fill="x", pady=(0, 5))

    username_entry = ctk.CTkEntry(
        form_inner,
        placeholder_text="Proxy username",
        height=40,
        font=ctk.CTkFont(size=13)
    )
    username_entry.pack(fill="x", pady=(0, 15))
    if REMOTE_USERNAME:
        username_entry.insert(0, REMOTE_USERNAME)

    # Password
    password_label = ctk.CTkLabel(
        form_inner,
        text="Password (Optional):",
        font=ctk.CTkFont(size=13, weight="bold"),
        anchor="w"
    )
    password_label.pack(fill="x", pady=(0, 5))

    password_entry = ctk.CTkEntry(
        form_inner,
        placeholder_text="Proxy password",
        height=40,
        font=ctk.CTkFont(size=13),
        show="•"
    )
    password_entry.pack(fill="x", pady=(0, 5))
    if REMOTE_PASSWORD:
        password_entry.insert(0, REMOTE_PASSWORD)

    # Info label
    info_label = ctk.CTkLabel(
        main_frame,
        text="💡 Leave username/password empty if proxy doesn't require authentication.\n"
             "Disable proxy to connect directly without a proxy server.",
        font=ctk.CTkFont(size=11),
        text_color="gray",
        justify="left"
    )
    info_label.pack(pady=(0, 20))

    # Buttons
    button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    button_frame.pack(fill="x")

    def save_settings():
        """Save proxy settings"""
        enabled = proxy_enabled_var.get()
        server = server_entry.get().strip()
        port = port_entry.get().strip()
        username = username_entry.get().strip()
        password = password_entry.get().strip()

        if enabled and (not server or not port):
            # Show error
            error_label = ctk.CTkLabel(
                main_frame,
                text="❌ Server address and port are required when proxy is enabled!",
                text_color="#ef4444",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            error_label.pack(before=button_frame, pady=(0, 10))
            dialog.after(3000, error_label.destroy)
            return

        # Validate port
        if enabled and port:
            try:
                port_num = int(port)
                if port_num < 1 or port_num > 65535:
                    raise ValueError()
            except ValueError:
                error_label = ctk.CTkLabel(
                    main_frame,
                    text="❌ Port must be a number between 1 and 65535!",
                    text_color="#ef4444",
                    font=ctk.CTkFont(size=12, weight="bold")
                )
                error_label.pack(before=button_frame, pady=(0, 10))
                dialog.after(3000, error_label.destroy)
                return

        # Configure proxy
        configure_proxy(
            server=server if server else None,
            port=int(port) if port else None,
            username=username if username else None,
            password=password if password else None,
            enabled=enabled
        )

        # Show success message
        success_label = ctk.CTkLabel(
            main_frame,
            text="✅ Proxy settings saved successfully!",
            text_color="#10b981",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        success_label.pack(before=button_frame, pady=(0, 10))

        # Close dialog after a short delay
        dialog.after(1000, dialog.destroy)

    def cancel_settings():
        """Cancel and close dialog"""
        dialog.destroy()

    cancel_button = ctk.CTkButton(
        button_frame,
        text="Cancel",
        command=cancel_settings,
        fg_color="transparent",
        border_width=2,
        border_color=("#cbd5e1", "#475569"),
        text_color=("#475569", "#cbd5e1"),
        hover_color=("#f1f5f9", "#334155"),
        height=40,
        font=ctk.CTkFont(size=13, weight="bold")
    )
    cancel_button.pack(side="left", fill="x", expand=True, padx=(0, 10))

    save_button = ctk.CTkButton(
        button_frame,
        text="💾 Save Settings",
        command=save_settings,
        fg_color="#3b82f6",
        hover_color="#2563eb",
        height=40,
        font=ctk.CTkFont(size=13, weight="bold")
    )
    save_button.pack(side="right", fill="x", expand=True)

    # Wait for dialog to close
    dialog.wait_window()


if __name__ == "__main__":
    start_proxy_server()
