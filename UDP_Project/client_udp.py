#!/usr/bin/env python3
"""
UDP Quiz Game Client
Terminal-based client for UDP quiz game
"""

import socket
import json
import time
import threading
import argparse
from typing import Dict

class UDPClient:
    def __init__(self, server_host='localhost', server_port=8888):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(1.0)
        
        self.username = None
        self.connected = False
        self.game_active = False
        self.current_question = None
        
    def connect(self, username: str):
        """Connect to server with username"""
        self.username = username
        join_msg = {
            "type": "join",
            "username": username
        }
        
        self.socket.sendto(
            json.dumps(join_msg).encode('utf-8'),
            (self.server_host, self.server_port)
        )
        
        # Wait for response
        try:
            data, _ = self.socket.recvfrom(1024)
            response = json.loads(data.decode('utf-8'))
            
            if response['type'] == 'joined':
                self.connected = True
                print(f"✓ Connected as {username}")
                return True
            elif response['type'] == 'error':
                print(f"✗ {response['message']}")
                return False
                
        except socket.timeout:
            print("✗ Connection timeout - server may be down")
            return False
        except json.JSONDecodeError:
            print("✗ Invalid response from server")
            return False
    
    def send_answer(self, question_id: int, answer: str, time_taken: float):
        """Send answer to server"""
        if self.connected:
            answer_msg = {
                "type": "answer",
                "username": self.username,
                "question_id": question_id,
                "answer": answer,
                "time": time_taken
            }
            
            self.socket.sendto(
                json.dumps(answer_msg).encode('utf-8'),
                (self.server_host, self.server_port)
            )
    
    def listen_for_messages(self):
        """Listen for incoming messages from server"""
        while self.connected:
            try:
                data, _ = self.socket.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                self.handle_server_message(message)
                
            except socket.timeout:
                continue
            except json.JSONDecodeError:
                continue
            except OSError:
                break
    
    def handle_server_message(self, message: Dict):
        """Handle different types of server messages"""
        msg_type = message['type']
        
        if msg_type == 'game_start':
            print("\n🎮 Game is starting! Get ready...")
            self.game_active = True
            
        elif msg_type == 'question':
            self.current_question = message
            print(f"\n{'='*60}")
            print(f"📝 Question {message['number']}: {message['text']}")
            print(f"{'='*60}")
            for option in message['options']:
                print(f"  {option}")
            print(f"{'='*60}")
            
            # Start timer and get answer
            start_time = time.time()
            answer = input("Your answer (A/B/C/D): ").strip().upper()
            time_taken = time.time() - start_time
            
            if answer in ['A', 'B', 'C', 'D']:
                self.send_answer(message['id'], answer, time_taken)
                print(f"✓ Answer sent! (Time: {time_taken:.1f}s)")
            else:
                print("✗ Invalid answer format")
            
        elif msg_type == 'result':
            print(f"\n📊 Result for Question {self.current_question['number'] if self.current_question else 'N/A'}:")
            print(f"  Correct answer: {message['correct']}")
            print(f"  Your answer: {message['your_answer'] or 'No answer'}")
            print(f"  Status: {'✓ CORRECT' if message['is_correct'] else '✗ WRONG'}")
            print(f"  Points earned: {message['points']}")
            print(f"  Total score: {message['total_score']}")
            
        elif msg_type == 'leaderboard':
            print(f"\n🏆 Current Leaderboard:")
            for i, player in enumerate(message['top3'], 1):
                print(f"  {i}. {player['username']}: {player['score']} pts")
                
        elif msg_type == 'end':
            print(f"\n{'='*60}")
            print("🎉 GAME OVER - Final Results!")
            print(f"{'='*60}")
            for i, player in enumerate(message['leaderboard'], 1):
                print(f"  {i}. {player['username']}: {player['score']} pts")
            
            if message['winner']:
                print(f"\n👑 Winner: {message['winner']}!")
            print(f"{'='*60}")
            
            self.connected = False
            self.game_active = False
    
    def start(self):
        """Start the client"""
        print(f"\n🎯 UDP Quiz Game Client")
        print(f"{'='*40}")
        
        # Get username and connect
        while not self.connected:
            username = input("Enter your username: ").strip()
            if username:
                if not self.connect(username):
                    print("Please try again with a different username\n")
            else:
                print("Username cannot be empty\n")
        
        # Start message listener
        listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        listener_thread.start()
        
        print(f"\n✅ Connected to server! Waiting for game to start...")
        print("Type 'quit' to exit at any time\n")
        
        # Main input loop
        try:
            while self.connected:
                user_input = input().strip().lower()
                if user_input == 'quit':
                    break
                time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.connected = False
            self.socket.close()
            print("👋 Goodbye!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='UDP Quiz Game Client')
    parser.add_argument('server_host', nargs='?', default='localhost',
                       help='Server hostname or IP (default: localhost)')
    parser.add_argument('--port', '-p', type=int, default=8888,
                       help='Server port (default: 8888)')
    
    args = parser.parse_args()
    
    client = UDPClient(server_host=args.server_host, server_port=args.port)
    client.start()