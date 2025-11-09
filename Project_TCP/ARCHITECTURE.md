# Architecture Overview

## 📐 System Design

### TCP Socket Architecture

```
┌─────────────────┐         TCP Socket (Port 8888)        ┌─────────────────┐
│  TCP Server     │◄──────────────────────────────────────►│  Client Bridge  │
│  server_tcp.py  │                                        │  client_tcp.py  │
│                 │                                        │                 │
│ • Game Logic    │                                        │ • HTTP Server   │
│ • Timing        │                                        │ • Message Queue │
│ • Scoring       │                                        │ • TCP Client    │
│ • Leaderboard   │                                        │                 │
└─────────────────┘                                        └─────────────────┘
                                                                       ▲
                                                                       │
                                                            HTTP (Port 8000)
                                                                       │
                                                              ┌─────────────────┐
                                                              │  Web Interface  │
                                                              │  web/*.html/js   │
                                                              │  - index.html   │
                                                              │  - style.css    │
                                                              │  - script.js     │
                                                              └─────────────────┘
```

## 🔧 Data Structures

### Player Data
```python
self.players = {
    "username": {
        "score": 0,      # Total score
        "answered": False # Has answered current question
    }
}
```

### Leaderboard Format
```python
[
    {"u": "username1", "s": 250},
    {"u": "username2", "s": 180},
    {"u": "username3", "s": 150}
]
```

## 📨 Message Protocol (JSON over TCP)

### Client → Server

#### Join
```json
{"type":"join","username":"Ahmed"}
```

#### Answer
```json
{"type":"answer","question_id":1,"answer":"A","time":2.3}
```

### Server → Client

#### Question
```json
{
    "type":"question",
    "id":1,
    "number":1,
    "text":"What does TCP stand for?",
    "options":["A) ...", "B) ...", "C) ...", "D) ..."],
    "timeout":30
}
```

#### Result
```json
{
    "type":"result",
    "correct":"B",
    "your_answer":"B",
    "is_correct":true,
    "points":95,
    "total_score":95
}
```

#### Leaderboard
```json
{
    "type":"leaderboard",
    "top3":[{"u":"Ali","s":250},{"u":"Ahmed","s":180},{"u":"Omar","s":150}]
}
```

#### End
```json
{
    "type":"end",
    "leaderboard":[...],
    "winner":"Ali"
}
```

## 🧮 Scoring Algorithm

```python
score = max(0, 100 - 3 × seconds_taken)
```

- **Correct answer in 5 seconds**: 85 points
- **Correct answer in 10 seconds**: 70 points
- **Correct answer in 20 seconds**: 40 points
- **Correct answer in 30+ seconds**: 10 points
- **Wrong answer**: 0 points

## 🎮 Game Flow

1. **Join Phase**
   - Clients connect via TCP (port 8888)
   - Server waits 5 seconds for players to join
   - Server broadcasts "game_start"

2. **Question Phase** (10 questions)
   - Server sends question to all clients
   - 30-second timer starts
   - Clients submit answers
   - Question ends when:
     - All clients answered OR
     - 30 seconds elapsed

3. **Result Phase**
   - Server calculates scores
   - Sends individual results to each client
   - Broadcasts top 3 leaderboard
   - Wait 3 seconds before next question

4. **End Phase**
   - Display final leaderboard
   - Announce winner

## 🔒 Thread Safety

All shared state access is protected with `threading.Lock`:

```python
with self.lock:
    # Access shared state
    self.players[username]['score'] += points
    self.answers[username] = (answer, time)
```

## 🌐 Network Configuration

- **Protocol**: TCP (reliable, ordered)
- **Server Port**: 8888
- **Client Port**: 8000 (HTTP)
- **Encoding**: UTF-8
- **Delimiter**: `\n` (newline)
- **Format**: JSON messages

## 🛠️ Technologies Used

- **Python 3.7+**
  - `socket` - TCP networking
  - `threading` - Concurrent client handling
  - `json` - Message serialization
  - `time` - Timing and delays

- **Web Technologies**
  - HTML5 - Structure
  - CSS3 - Styling (Gradients, Animations)
  - Vanilla JavaScript - Client logic

## 🎯 Design Principles

1. **Modularity**: Separate concerns (server, client, web)
2. **Reliability**: TCP guarantees message delivery
3. **Thread Safety**: Locks protect shared state
4. **Scalability**: Multiple concurrent players
5. **Responsiveness**: 500ms polling for quick updates
6. **User Experience**: Real-time leaderboard, timer, animations

