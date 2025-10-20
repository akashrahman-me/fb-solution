#!/usr/bin/env python3
"""
Simple HTTP proxy that forwards requests to an upstream authenticated proxy.
"""
import socket
import select
import threading
import base64
from urllib.parse import urlparse

# --- Configuration ---
LOCAL_PROXY_HOST = "127.0.0.1"
LOCAL_PROXY_PORT = 8080

# Residential Proxy Credentials
# ---------------------
# REMOTE_SERVER = "p.webshare.io"
# REMOTE_PORT = 80
# REMOTE_USERNAME = "rqsgbzmp-rotate"
# REMOTE_PASSWORD = "yag0ewjl9tws"

# Datacenter Proxy Credentials
# ---------------------
REMOTE_SERVER = "142.111.48.253"
REMOTE_PORT = 7030
REMOTE_USERNAME = "lmmwyrac"
REMOTE_PASSWORD = "fi17jsine73g"
# ---------------------

# Base64 encode the credentials
PROXY_AUTH = base64.b64encode(f"{REMOTE_USERNAME}:{REMOTE_PASSWORD}".encode()).decode()

class ProxyThread(threading.Thread):
    def __init__(self, client_socket, client_address):
        threading.Thread.__init__(self)
        self.client = client_socket
        self.client_address = client_address
        self.daemon = True

    def run(self):
        try:
            # Receive the client's request
            request = self.client.recv(4096)
            if not request:
                return

            request_str = request.decode('latin-1', errors='ignore')
            print(f"\n[{self.client_address[0]}] Request:\n{request_str.split('\\r\\n')[0]}")

            # Add Proxy-Authorization header if not present
            lines = request_str.split('\r\n')
            has_proxy_auth = any('Proxy-Authorization' in line for line in lines)
            
            if not has_proxy_auth:
                # Insert Proxy-Authorization after the first line
                lines.insert(1, f'Proxy-Authorization: Basic {PROXY_AUTH}')
                request_str = '\r\n'.join(lines)
                request = request_str.encode('latin-1')
                print(f"[{self.client_address[0]}] Added Proxy-Authorization header")

            # Connect to the upstream proxy
            upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            upstream.settimeout(10)
            
            try:
                print(f"[{self.client_address[0]}] Connecting to upstream proxy {REMOTE_SERVER}:{REMOTE_PORT}")
                upstream.connect((REMOTE_SERVER, REMOTE_PORT))
                
                # Send the modified request to upstream proxy
                upstream.sendall(request)
                
                # Relay data between client and upstream proxy
                self.relay_data(self.client, upstream)
                
            except socket.timeout:
                print(f"[{self.client_address[0]}] Connection to upstream proxy timed out")
                self.client.send(b"HTTP/1.1 504 Gateway Timeout\r\n\r\n")
            except ConnectionRefusedError:
                print(f"[{self.client_address[0]}] Upstream proxy refused connection")
                self.client.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            except Exception as e:
                print(f"[{self.client_address[0]}] Error connecting to upstream: {e}")
                self.client.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            finally:
                upstream.close()
                
        except Exception as e:
            print(f"[{self.client_address[0]}] Error: {e}")
        finally:
            self.client.close()

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
                        else:
                            client.send(data)
                    except:
                        return
                        
        except Exception as e:
            print(f"Relay error: {e}")


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

