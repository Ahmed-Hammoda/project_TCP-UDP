#!/usr/bin/env python3
"""
UDP Quiz Game Server
Handles multiple clients via UDP, manages game flow, scoring, and leaderboards
"""

import socket
import json
import time
import os
import threading
from typing import Dict, List, Tuple

class UDPServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        
        # Store client addresses and their data
        self.clients: Dict[tuple, Dict] = {}  # { (ip, port): {username, score, last_seen} }
        self.players: Dict[str, Dict] = {}    # { username: {score, address} }
        self.questions = self.load_questions()
        self.current_question = 0
        self.game_active = False
        self.answers: Dict[str, Tuple[str, float]] = {}
        self.lock = threading.Lock()
        
    def load_questions(self) -> List[Dict]:
        """Load quiz questions from JSON file"""
        try:
            with open('questions.json', 'r', encoding='utf-8') as f:
                questions = json.load(f)
            print(f"✓ Loaded {len(questions)} questions")
            return questions
        except FileNotFoundError:
            print("⚠ questions.json not found, using default questions")
            return self._get_default_questions()
    
    def _get_default_questions(self) -> List[Dict]:
        """Fallback default questions"""
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
            }
        ]
    
    def send_message(self, address: tuple, message: Dict):
        """Send JSON message to client"""
        try:
            msg = json.dumps(message).encode('utf-8')
            self.socket.sendto(msg, address)
        except Exception as e:
            print(f"Error sending to {address}: {e}")
    
    def broadcast(self, message: Dict, exclude: tuple = None):
        """Broadcast message to all connected clients"""
        with self.lock:
            for client_addr in list(self.clients.keys()):
                if client_addr != exclude:
                    self.send_message(client_addr, message)
    
    def calculate_score(self, time_taken: float) -> int:
        """Calculate score based on time taken"""
        return max(0, int(100 - 3 * time_taken))
    
    def get_leaderboard(self, top_n: int = 3) -> List[Dict]:
        """Get top N players"""
        with self.lock:
            sorted_players = sorted(self.players.items(), 
                                   key=lambda x: x[1]['score'], 
                                   reverse=True)
            return [{"username": username, "score": data['score']} 
                   for username, data in sorted_players[:top_n]]
    
    def handle_join(self, username: str, address: tuple):
        """Handle player joining"""
        with self.lock:
            if username in self.players:
                self.send_message(address, {
                    "type": "error",
                    "message": "Username already taken"
                })
                return
            
            self.clients[address] = {"username": username, "last_seen": time.time()}
            self.players[username] = {"score": 0, "address": address}
        
        print(f"✓ {username} joined from {address[0]}:{address[1]}")
        print(f"   Total players: {len(self.players)}")
        
        self.send_message(address, {
            "type": "joined",
            "message": f"Welcome {username}! Waiting for game to start..."
        })
    
    def handle_answer(self, username: str, question_id: int, answer: str, time_taken: float):
        """Handle player answer"""
        with self.lock:
            if username not in self.answers and self.game_active:
                self.answers[username] = (answer, time_taken)
                print(f"   ✓ {username} answered: {answer} ({time_taken:.1f}s)")
    
    def cleanup_clients(self):
        """Remove inactive clients"""
        current_time = time.time()
        with self.lock:
            inactive_clients = []
            for addr, client_data in list(self.clients.items()):
                if current_time - client_data['last_seen'] > 30:  # 30 seconds timeout
                    inactive_clients.append(addr)
            
            for addr in inactive_clients:
                username = self.clients[addr]['username']
                del self.clients[addr]
                if username in self.players:
                    del self.players[username]
                print(f"✗ {username} timed out")
    
    def update_client_activity(self, address: tuple):
        """Update client last seen time"""
        with self.lock:
            if address in self.clients:
                self.clients[address]['last_seen'] = time.time()
    
    def run_game(self):
        """Main game loop"""
        print("\n🎮 Starting game...")
        self.game_active = True
        
        self.broadcast({"type": "game_start", "message": "Game is starting!"})
        time.sleep(2)
        
        for q_num, question in enumerate(self.questions, 1):
            print(f"\n📝 Question {q_num}/{len(self.questions)}: {question['text']}")
            
            with self.lock:
                self.answers.clear()
            
            # Send question to all clients
            self.broadcast({
                "type": "question",
                "id": question["id"],
                "number": q_num,
                "text": question["text"],
                "options": question["options"],
                "timeout": 30
            })
            
            # Wait for answers
            start_time = time.time()
            answered_count = 0
            total_players = len(self.players)
            
            while time.time() - start_time < 30:
                with self.lock:
                    answered_count = len(self.answers)
                if answered_count == total_players:
                    break
                print(f"   Waiting for answers... {answered_count}/{total_players}", end='\r')
                time.sleep(1)
            
            print(f"\n   ⏱️  Question ended - {answered_count}/{total_players} answered")
            
            # Calculate results
            with self.lock:
                for username, player_data in self.players.items():
                    if username in self.answers:
                        answer, answer_time = self.answers[username]
                        is_correct = answer == question["correct"]
                        points = self.calculate_score(answer_time) if is_correct else 0
                    else:
                        answer = None
                        is_correct = False
                        points = 0
                    
                    player_data['score'] += points
                    
                    # Send individual result
                    if username in self.players:
                        self.send_message(player_data['address'], {
                            "type": "result",
                            "correct": question["correct"],
                            "your_answer": answer,
                            "is_correct": is_correct,
                            "points": points,
                            "total_score": player_data['score']
                        })
            
            # Show leaderboard
            leaderboard = self.get_leaderboard(3)
            print("\n🏆 Current Top 3:")
            for i, entry in enumerate(leaderboard, 1):
                print(f"   {i}. {entry['username']}: {entry['score']} pts")
            
            self.broadcast({
                "type": "leaderboard",
                "top3": leaderboard
            })
            
            # Wait for next question
            if q_num < len(self.questions):
                input("\n⏸ Press Enter to proceed to next question...")
        
        # Game over
        self.game_active = False
        final_leaderboard = self.get_leaderboard(len(self.players))
        winner = final_leaderboard[0] if final_leaderboard else None
        
        print("\n" + "="*50)
        print("🎉 GAME OVER - Final Results:")
        print("="*50)
        for i, entry in enumerate(final_leaderboard, 1):
            print(f"{i}. {entry['username']}: {entry['score']} pts")
        
        if winner:
            print(f"\n👑 Winner: {winner['username']} with {winner['score']} points!")
        
        self.broadcast({
            "type": "end",
            "leaderboard": final_leaderboard,
            "winner": winner['username'] if winner else None
        })
    
    def start(self):
        """Start the UDP server"""
        print(f"\n{'='*60}")
        print(f"🎯 UDP Quiz Server Started!")
        print(f"{'='*60}")
        print(f"   Host: {self.host}")
        print(f"   Port: {self.port}")
        print(f"{'='*60}")
        print(f"\n⏳ Waiting for players to join...")
        print(f"   Type 'start' and press Enter to begin the game")
        print(f"{'='*60}\n")
        
        # Start game in separate thread when ready
        def game_starter():
            while True:
                cmd = input().strip().lower()
                if cmd == 'start':
                    if len(self.players) > 0:
                        self.run_game()
                        break
                    else:
                        print("   ⚠️  No players connected yet!")
        
        game_thread = threading.Thread(target=game_starter, daemon=True)
        game_thread.start()
        
        # Main receive loop
        try:
            while True:
                try:
                    data, address = self.socket.recvfrom(1024)
                    message = json.loads(data.decode('utf-8'))
                    
                    self.update_client_activity(address)
                    
                    if message['type'] == 'join':
                        self.handle_join(message['username'], address)
                    elif message['type'] == 'answer':
                        self.handle_answer(
                            message['username'],
                            message['question_id'],
                            message['answer'],
                            message['time']
                        )
                    elif message['type'] == 'ping':
                        self.send_message(address, {"type": "pong"})
                    
                    # Cleanup every 10 received messages
                    if hash(str(address)) % 10 == 0:
                        self.cleanup_clients()
                        
                except json.JSONDecodeError:
                    continue
                except KeyError:
                    continue
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Server shutting down...")
        finally:
            self.socket.close()

if __name__ == "__main__":
    server = UDPServer()
    server.start()