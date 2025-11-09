# TCP Quiz Game

A real-time multiplayer quiz game built with Python TCP sockets and a modern web interface.

## 🎮 Overview

This project demonstrates a TCP-based quiz game where multiple players can compete in real-time. The game consists of:

- **TCP Server** (`server_tcp.py`) - Manages game logic, timing, scoring, and leaderboards
- **TCP Client Bridge** (`client_tcp.py`) - Connects to the server and serves a web interface
- **Web Interface** (`web/`) - Beautiful, responsive frontend with gradient design

## 📁 Project Structure

```
quiznet-tcp/
├── server_tcp.py              # TCP server – controls game, timing, scoring, leaderboard
├── client_tcp.py              # TCP client bridge – connects to server & serves web interface
│
├── web/                       # Frontend files (HTML/CSS/JS)
│   ├── index.html             # Web interface for players
│   ├── style.css              # Gradient design + animations + responsive layout
│   └── script.js              # Client-side game logic and live updates
│
├── data/
│   └── questions.json         # 10 quiz questions in JSON format
│
├── utils/
│   ├── __init__.py
│   └── messages.py            # Shared helper for JSON encoding/decoding
│
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── ARCHITECTURE.md            # System architecture documentation
└── CHANGES.md                 # Change history
```

## ✨ Features

- **Real-time multiplayer gameplay** with TCP sockets
- **Interactive web interface** with gradient design
- **Live scoring system** based on response time
- **Leaderboard updates** after each question
- **Timer countdown** for each question (30 seconds)
- **Beautiful UI** with animations and responsive layout

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- A modern web browser

### Installation

1. Clone or download this repository

2. Install Python dependencies (if any custom libraries are added later):
   ```bash
   pip install -r requirements.txt
   ```

### Running the Game

1. **Start the Server** (Terminal 1):
   ```bash
   python server_tcp.py
   ```
   - Server will wait for players to join
   - You'll see messages like: `✓ Ahmed joined from (host, port) (Total: 1 players)`
   - Type `start` and press Enter when ready to begin the game

2. **Start the Client Bridge** (Terminal 2):
   
   **For local connection (same PC as server):**
   ```bash
   python client_tcp.py
   ```
   
   **For network connection (different PC on same network):**
   ```bash
   python client_tcp.py 192.168.1.100
   ```
   (Replace `192.168.1.100` with the server's IP address shown when server starts)
   
   Or use the `--server` flag:
   ```bash
   python client_tcp.py --server 192.168.1.100
   ```
   
   - Automatically opens browser with the game interface
   - Connect by entering a username on the login screen

### Playing the Game

1. The browser should open automatically when you run `client_tcp.py`
2. Enter your username on the login screen
3. Wait for other players to join (optional)
4. When everyone is ready, go back to the server terminal and type `start`
5. Answer questions quickly to maximize your score
6. Watch your score and position on the leaderboard
7. The winner is announced at the end!

## 🎯 How It Works

### Server (`server_tcp.py`)

- Listens on port `8888` for client connections
- Connection-oriented TCP (reliable and ordered data delivery)
- Manages multiple client connections using threading
- Player data structure: `{username: {"score": int, "answered": bool}}`
- Broadcasts questions to all connected players
- Scoring formula: `score = max(0, 100 - 3 × seconds_taken)`
- Tracks scores based on response time (faster = more points)
- Each question lasts 30 seconds OR ends early if all clients answer
- Calculates and broadcasts leaderboards after each question
- Runs a complete game session with 10 questions
- Message protocol: JSON over TCP with newline delimiter

### Client Bridge (`client_tcp.py`)

- Connects to the TCP server on `localhost:8888`
- Serves the web interface via HTTP on port `8000`
- Bridges HTTP requests from the browser to TCP messages
- Message queue system for async communication
- Queues incoming messages from the server
- Provides endpoints: `/api/messages`, `/api/connect`, `/api/answer`

### Web Interface (`web/`)

- **HTML**: Login screen, game screen with questions and leaderboard
- **CSS**: Modern gradient design with smooth animations
- **JavaScript**: Polls for server messages, handles game state, updates UI

## 📋 Default Configuration

- **Server Host**: `0.0.0.0` (accepts connections from any IP)
- **Server Port**: `8888`
- **Web Port**: `8000`
- **Questions**: 10 TCP/networking related questions
- **Time per Question**: 30 seconds

## 🛠️ Customization

### Adding More Questions

Edit `data/questions.json`:
```json
{
    "id": 11,
    "text": "Your question here?",
    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "correct": "A"
}
```

### Changing Ports

Edit the initialization in `server_tcp.py` and `client_tcp.py`:
```python
# Server
QuizServer(host='0.0.0.0', port=8888)

# Client
QuizClientBridge(server_host='localhost', server_port=8888, web_port=8000)
```

## 🧠 Game Logic

- **Scoring**: `score = max(0, 100 - 3 × time_seconds)` for correct answers
- **Answer Collection**: Server waits for all players or 30 seconds timeout
- **Leaderboard Format**: `{u: username, s: score}` - shows top 3 players after each question
- **Player Data**: `{username: {"score": int, "answered": bool}}`
- **Winner**: Highest score at the end of all 10 questions
- **Connection**: TCP sockets on port 8888, encoding UTF-8, JSON messages

## 📝 License

This project is provided as-is for educational purposes.

## 🤝 Contributing

Feel free to fork, modify, and improve this project!

---

**Enjoy the game! 🎉**
