#!/usr/bin/env python3
"""
TCP Quiz Game Client Bridge
Connects to TCP server and serves HTML interface via HTTP

Architecture:
- Bridges TCP socket to WebSocket-like HTTP API
- Connects to server on port 8888
- Serves web interface on port 8000
- Message queue system for async communication
- Endpoints: /api/connect, /api/answer, /api/messages
"""

import socket
import threading
import json
import http.server
import socketserver
import sys
import argparse
from urllib.parse import parse_qs

class QuizClientBridge:
    def __init__(self, server_host='localhost', server_port=8888, web_port=8000):
        self.server_host = server_host
        self.server_port = server_port
        self.web_port = web_port
        self.tcp_socket = None
        self.connected = False
        self.username = None
        self.message_queue = []
        self.lock = threading.Lock()
        
    def connect_to_server(self, username: str) -> bool:
        """Connect to TCP quiz server"""
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((self.server_host, self.server_port))
            self.username = username
            
            join_msg = json.dumps({"type": "join", "username": username}) + '\n'
            self.tcp_socket.sendall(join_msg.encode('utf-8'))
            
            self.connected = True
            print(f"✓ Connected as {username}")
            
            receiver_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receiver_thread.start()
            
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def receive_messages(self):
        """Receive messages from server"""
        buffer = ""
        while self.connected:
            try:
                data = self.tcp_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                    
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    try:
                        msg = json.loads(line)
                        with self.lock:
                            self.message_queue.append(msg)
                        print(f"📨 Received: {msg['type']}")
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                print(f"Error receiving: {e}")
                break
        
        self.connected = False
        print("✗ Disconnected from server")
    
    def send_answer(self, question_id: int, answer: str, time_taken: float):
        """Send answer to server"""
        if self.connected:
            try:
                msg = json.dumps({
                    "type": "answer",
                    "question_id": question_id,
                    "answer": answer,
                    "time": time_taken
                }) + '\n'
                self.tcp_socket.sendall(msg.encode('utf-8'))
                print(f"📤 Sent answer: {answer} ({time_taken:.1f}s)")
            except Exception as e:
                print(f"Error sending answer: {e}")
    
    def get_messages(self):
        """Get all queued messages"""
        with self.lock:
            messages = self.message_queue.copy()
            self.message_queue.clear()
            return messages
    
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        if self.tcp_socket:
            self.tcp_socket.close()

# Parse command line arguments for server host
def parse_args():
    parser = argparse.ArgumentParser(description='TCP Quiz Game Client')
    parser.add_argument('server_host', nargs='?', default='localhost',
                       help='Server IP address or hostname (default: localhost)')
    parser.add_argument('--server', '-s', dest='server_host_alt',
                       help='Server IP address or hostname')
    parser.add_argument('--port', '-p', type=int, default=8888,
                       help='Server port (default: 8888)')
    args = parser.parse_args()
    
    # Use --server value if provided, otherwise use positional argument
    server_host = args.server_host_alt if args.server_host_alt else args.server_host
    return server_host, args.port

bridge = None

class QuizHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for web interface"""
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/api/messages':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            messages = bridge.get_messages()
            self.wfile.write(json.dumps({"messages": messages}).encode())
            return
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "connected": bridge.connected,
                "username": bridge.username
            }).encode())
            return
        
        return super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/connect':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            username = params.get('username', [''])[0]
            
            success = bridge.connect_to_server(username)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": success}).encode())
        
        elif self.path == '/api/answer':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            bridge.send_answer(data['question_id'], data['answer'], data['time'])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode())

def start_web_server():
    """Start HTTP server for web interface"""
    import os
    import webbrowser
    import errno
    
    # Change directory to web folder to serve static files
    web_dir = os.path.join(os.path.dirname(__file__), 'web')
    os.chdir(web_dir)
    
    handler = QuizHTTPHandler
    httpd = None
    port = bridge.web_port
    # Try to bind; if busy, increment port to allow multiple clients on same PC
    while httpd is None:
        try:
            httpd = socketserver.TCPServer(("", port), handler)
        except OSError as e:
            if hasattr(e, 'errno') and e.errno == errno.EADDRINUSE:
                print(f"Port {port} in use, trying {port+1}...")
                port += 1
                continue
            raise
    # Update chosen port on bridge for logging
    bridge.web_port = port
    url = f"http://localhost:{port}"
    print(f"\n🌐 Web interface: {url}")
    print(f"📡 Connecting to server: {bridge.server_host}:{bridge.server_port}")
    print("Opening browser automatically...")
    webbrowser.open(url)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()

if __name__ == "__main__":
    # Parse command line arguments
    server_host, server_port = parse_args()
    
    # Initialize bridge with server host from command line (global variable)
    bridge = QuizClientBridge(server_host=server_host, server_port=server_port)
    
    try:
        start_web_server()
    except KeyboardInterrupt:
        print("\n\n🛑 Client shutting down...")
        if bridge:
            bridge.disconnect()
