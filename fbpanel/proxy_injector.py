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

# --- Configuration ---
LOCAL_PROXY_HOST = "127.0.0.1"
LOCAL_PROXY_PORT = 8080

# Residential Proxy Credentials
# ---------------------
REMOTE_SERVER = "aus.360s5.com"
REMOTE_PORT = 3600
REMOTE_USERNAME = "75072370-zone-custom-region-KG"
REMOTE_PASSWORD = "G8Vmo6ac"
# Residential Proxy Credentials
# ---------------------
# REMOTE_SERVER = "aus.360s5.com"
# REMOTE_PORT = 3600
# REMOTE_USERNAME = "75072370-zone-custom"
# REMOTE_PASSWORD = "G8Vmo6ac"

# Datacenter Proxy Credentials
# ---------------------
# REMOTE_SERVER = "142.111.48.253"
# REMOTE_PORT = 7030
# REMOTE_USERNAME = "lmmwyrac"
# REMOTE_PASSWORD = "fi17jsine73g"
# ---------------------

# Base64 encode the credentials
PROXY_AUTH = base64.b64encode(f"{REMOTE_USERNAME}:{REMOTE_PASSWORD}".encode()).decode()

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

            # Add Proxy-Authorization header if not present
            lines = request_str.split('\r\n')
            has_proxy_auth = any('Proxy-Authorization' in line for line in lines)
            
            if not has_proxy_auth:
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
        finally:
            self.client.close()
            self.print_stats()

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
            print(f"🌐 {self.url} | ⬆️ {self.format_bytes(self.bytes_sent)} | ⬇️ {self.format_bytes(self.bytes_received)} | ✅ {self.format_bytes(total)}")

    def relay_data(self, client, upstream):
        """Relay data between client and upstream proxy"""
        try:
            sockets = [client, upstream]
            timeout = 60
            
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
                            upstream.send(data)
                            self.bytes_sent += len(data)
                        else:
                            client.send(data)
                            self.bytes_received += len(data)
                    except:
                        return
                        
        except Exception as e:
            pass


def start_proxy_server():
    """Start the local proxy server"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((LOCAL_PROXY_HOST, LOCAL_PROXY_PORT))
        server.listen(100)
        
        print(f"✓ Proxy server started on {LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}")
        print(f"✓ Forwarding to: {REMOTE_SERVER}:{REMOTE_PORT}")
        print(f"✓ Press Ctrl+C to stop\n")
        
        while True:
            client_socket, client_address = server.accept()
            proxy_thread = ProxyThread(client_socket, client_address)
            proxy_thread.start()
            
    except KeyboardInterrupt:
        print("\n\nShutting down proxy server...")
    except Exception as e:
        print(f"Error starting proxy server: {e}")
    finally:
        server.close()
        print("Proxy server stopped.")


if __name__ == "__main__":
    start_proxy_server()
