#!/usr/bin/env python3
"""
TCP Quiz Game Server
Handles multiple clients, manages game flow, scoring, and leaderboards

Architecture:
- Uses Python TCP sockets on port 8888
- Connection-oriented TCP (reliable and ordered)
- Threading: Each client handled via separate thread
- Message protocol: JSON over TCP with newline delimiter
- Scoring: score = max(0, 100 - 3 * seconds_taken)
- Player data: {username: {"score": int, "answered": bool}}
"""

import socket
import threading
import json
import time
import os
from typing import Dict, List, Tuple

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote address to determine local IP
        # (doesn't actually send data, just determines route)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            # Fallback: get hostname and resolve it
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
        except Exception:
            return "127.0.0.1"

class QuizServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.clients: Dict[str, socket.socket] = {}
        # Store player data as {username: {"score": int, "answered": bool}}
        self.players: Dict[str, Dict] = {}
        self.answers: Dict[str, Tuple[str, float]] = {}
        self.lock = threading.Lock()
        self.questions = self.load_questions()
        self.current_question = 0
        
    def load_questions(self) -> List[Dict]:
        """Load quiz questions from JSON file"""
        try:
            # Try to load from data/questions.json
            json_path = os.path.join(os.path.dirname(__file__), 'data', 'questions.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            print(f"✓ Loaded {len(questions)} questions from {json_path}")
            return questions
        except FileNotFoundError:
            print(f"⚠ Warning: {json_path} not found, using default questions")
            return self._get_default_questions()
        except Exception as e:
            print(f"⚠ Error loading questions: {e}, using default questions")
            return self._get_default_questions()
    
    def _get_default_questions(self) -> List[Dict]:
        """Fallback default questions if JSON file is not available"""
        return [
            {
                "id": 1,
                "text": "What does TCP stand for?",
                "options": ["A) Transfer Control Protocol", "B) Transmission Control Protocol", 
                           "C) Transport Communication Protocol", "D) Technical Computer Protocol"],
                "correct": "B"
            },
            {
                "id": 2,
                "text": "Which layer of OSI model does TCP operate?",
                "options": ["A) Physical", "B) Network", "C) Transport", "D) Application"],
                "correct": "C"
            },
            {
                "id": 3,
                "text": "What is the maximum size of TCP header?",
                "options": ["A) 20 bytes", "B) 40 bytes", "C) 60 bytes", "D) 80 bytes"],
                "correct": "C"
            },
            {
                "id": 4,
                "text": "TCP is a _____ protocol",
                "options": ["A) Connectionless", "B) Connection-oriented", "C) Stateless", "D) Unreliable"],
                "correct": "B"
            },
            {
                "id": 5,
                "text": "Which algorithm does TCP use for congestion control?",
                "options": ["A) Dijkstra", "B) Bellman-Ford", "C) Slow Start", "D) Quick Sort"],
                "correct": "C"
            },
            {
                "id": 6,
                "text": "What is the default TCP window size?",
                "options": ["A) 32 KB", "B) 64 KB", "C) 128 KB", "D) 256 KB"],
                "correct": "B"
            },
            {
                "id": 7,
                "text": "TCP uses _____ to ensure reliable delivery",
                "options": ["A) Acknowledgments", "B) Broadcasts", "C) Multicasts", "D) Floods"],
                "correct": "A"
            },
            {
                "id": 8,
                "text": "What is the three-way handshake?",
                "options": ["A) SYN, ACK, FIN", "B) SYN, SYN-ACK, ACK", "C) ACK, SYN, FIN", "D) FIN, ACK, SYN"],
                "correct": "B"
            },
            {
                "id": 9,
                "text": "Which port number range is for well-known services?",
                "options": ["A) 0-1023", "B) 1024-49151", "C) 49152-65535", "D) All of above"],
                "correct": "A"
            },
            {
                "id": 10,
                "text": "TCP provides _____ delivery of data",
                "options": ["A) Ordered", "B) Unordered", "C) Random", "D) Partial"],
                "correct": "A"
            }
        ]
    
    def send_message(self, client_socket: socket.socket, message: Dict):
        """Send JSON message to client"""
        try:
            msg = json.dumps(message) + '\n'
            client_socket.sendall(msg.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def broadcast(self, message: Dict, exclude: str = None):
        """Broadcast message to all clients"""
        with self.lock:
            for username, client_socket in list(self.clients.items()):
                if username != exclude:
                    self.send_message(client_socket, message)
    
    def calculate_score(self, time_taken: float) -> int:
        """Calculate score based on time taken: score = max(0, 100 - 3 * seconds_taken)"""
        return max(0, int(100 - 3 * time_taken))
    
    def get_leaderboard(self, top_n: int = 3) -> List[Dict]:
        """Get top N players - returns list of {u: username, s: score}"""
        with self.lock:
            sorted_players = sorted(self.players.items(), 
                                   key=lambda x: x[1]['score'], 
                                   reverse=True)
            return [{"u": username, "s": player_data['score']} 
                   for username, player_data in sorted_players[:top_n]]
    
    def handle_client(self, client_socket: socket.socket, address):
        """Handle individual client connection"""
        username = None
        buffer = ""
        
        try:
            # First, handle the join message
            while username is None:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                    
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    try:
                        msg = json.loads(line)
                        if msg['type'] == 'join':
                            username = msg['username']
                            with self.lock:
                                self.clients[username] = client_socket
                                # Initialize player: {username: {"score": 0, "answered": False}}
                                self.players[username] = {"score": 0, "answered": False}
                                player_count = len(self.clients)
                            print(f"✓ {username} joined from {address} (Total: {player_count} players)")
                            self.send_message(client_socket, {
                                "type": "joined",
                                "message": f"Welcome {username}! Waiting for game to start..."
                            })
                            break
                    except json.JSONDecodeError:
                        pass
                    except KeyError:
                        pass
            
            # Now keep connection alive to receive other messages
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                    
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    try:
                        msg = json.loads(line)
                        if msg['type'] == 'answer':
                            with self.lock:
                                if username not in self.answers:
                                    self.answers[username] = (msg['answer'], msg['time'])
                                    self.players[username]['answered'] = True
                                    print(f"   ✓ {username} answered: {msg['answer']} ({msg['time']:.1f}s)")
                    except (json.JSONDecodeError, KeyError):
                        pass
                        
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            if username:
                with self.lock:
                    if username in self.clients:
                        del self.clients[username]
                    if username in self.players:
                        del self.players[username]
                print(f"✗ {username} disconnected")
            client_socket.close()
    
    def run_game(self):
        """Main game loop"""
        print("\n🎮 Waiting for players to join...")
        print("   Type 'start' and press Enter when ready to begin the game")
        
        # Wait for manual start command
        while True:
            user_input = input()
            if user_input.lower().strip() == 'start':
                with self.lock:
                    player_count = len(self.clients)
                if player_count == 0:
                    print("   ⚠️ No players connected yet. Wait for players to join.")
                    continue
                break
        
        print(f"\n🚀 Game starting with {player_count} players!")
        self.broadcast({"type": "game_start", "message": "Game is starting!"})
        time.sleep(2)
        
        for q_num, question in enumerate(self.questions, 1):
            print(f"\n📝 Question {q_num}/10: {question['text']}")
            
            with self.lock:
                self.answers.clear()
            
            self.broadcast({
                "type": "question",
                "id": question["id"],
                "number": q_num,
                "text": question["text"],
                "options": question["options"],
                "timeout": 30
            })
            
            # Reset answered flag for all players
            with self.lock:
                for username in self.players:
                    self.players[username]['answered'] = False
            
            start_time = time.time()
            while time.time() - start_time < 30:
                with self.lock:
                    if len(self.answers) == len(self.clients):
                        break
                time.sleep(0.1)
            
            # End question after 30 seconds if not all answered
            elapsed = time.time() - start_time
            if elapsed >= 30:
                print(f"   ⏱️ Timeout after 30 seconds")
            
            # Calculate and send results to everyone (0 points if no answer)
            with self.lock:
                last_points_map: Dict[str, int] = {}
                for username in list(self.players.keys()):
                    if username in self.answers:
                        answer, answer_time = self.answers[username]
                        is_correct = answer == question["correct"]
                        points = self.calculate_score(answer_time) if is_correct else 0
                    else:
                        answer = None
                        is_correct = False
                        points = 0
                    last_points_map[username] = points
                    self.players[username]['score'] += points
                    self.send_message(self.clients[username], {
                        "type": "result",
                        "correct": question["correct"],
                        "your_answer": answer,
                        "is_correct": is_correct,
                        "points": points,
                        "total_score": self.players[username]['score']
                    })
            
            leaderboard = self.get_leaderboard(3)
            print("\n🏆 Top 3:")
            for i, entry in enumerate(leaderboard, 1):
                print(f"   {i}. {entry['u']}: {entry['s']} pts")
            
            self.broadcast({
                "type": "leaderboard",
                "top3": leaderboard
            })

            # Send per-client waiting info (rank, last points, total) and wait for operator 'next'
            with self.lock:
                # Build full leaderboard to compute ranks
                full_board = sorted(
                    ((u, pdata['score']) for u, pdata in self.players.items()),
                    key=lambda it: it[1],
                    reverse=True
                )
                username_to_rank = {u: (i + 1) for i, (u, _) in enumerate(full_board)}
                for username, client in list(self.clients.items()):
                    self.send_message(client, {
                        "type": "wait",
                        "rank": username_to_rank.get(username, None),
                        "last_points": last_points_map.get(username, 0),
                        "total_score": self.players[username]['score']
                    })

            print("\n⏸ Waiting... type 'next' and press Enter to proceed to the next question")
            while True:
                user_input = input()
                if user_input.lower().strip() == 'next':
                    break
        
        final_leaderboard = self.get_leaderboard(len(self.clients))
        winner = final_leaderboard[0] if final_leaderboard else None
        
        print("\n" + "="*50)
        print("🎉 GAME OVER - Final Results:")
        print("="*50)
        for i, entry in enumerate(final_leaderboard, 1):
            print(f"{i}. {entry['u']}: {entry['s']} pts")
        
        if winner:
            print(f"\n👑 Winner: {winner['u']} with {winner['s']} points!")
        
        self.broadcast({
            "type": "end",
            "leaderboard": final_leaderboard,
            "winner": winner['u'] if winner else None
        })
    
    
    def start(self):
        """Start the server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        # Get and display local IP address for network connections
        local_ip = get_local_ip()
        print(f"\n{'='*60}")
        print(f"🌐 TCP Quiz Server started!")
        print(f"{'='*60}")
        print(f"   Server IP: {local_ip}")
        print(f"   Port: {self.port}")
        print(f"   Binding: {self.host}:{self.port}")
        print(f"{'='*60}")
        print(f"\n📋 For other computers to connect:")
        print(f"   Run: python client_tcp.py {local_ip}")
        print(f"   Or: python client_tcp.py --server {local_ip}")
        print(f"\n⏳ Waiting for players to connect...")
        print(f"{'='*60}\n")
        
        game_thread = threading.Thread(target=self.run_game, daemon=True)
        game_thread.start()
        
        try:
            while True:
                client_socket, address = server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("\n\n🛑 Server shutting down...")
        finally:
            server_socket.close()

if __name__ == "__main__":
    server = QuizServer()
    server.start()
