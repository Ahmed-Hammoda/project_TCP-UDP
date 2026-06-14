# 🎮 Real-Time Multiplayer Quiz Game — TCP & UDP

> A networked, multiplayer trivia game implemented **twice from scratch** — once over **TCP** and once over **UDP** — to study, measure, and compare connection-oriented vs. connectionless transport protocols in a real application.

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.7%2B-3776AB?logo=python&logoColor=white" alt="Python 3.7+">
  <img src="https://img.shields.io/badge/Protocols-TCP%20%26%20UDP-1e88e5" alt="TCP & UDP">
  <img src="https://img.shields.io/badge/Sockets-Raw%20BSD%20Sockets-success" alt="Sockets">
  <img src="https://img.shields.io/badge/Concurrency-Multithreaded-orange" alt="Multithreaded">
  <img src="https://img.shields.io/badge/Dependencies-Standard%20Library%20Only-brightgreen" alt="Zero dependencies">
</p>

---

## 📌 Overview

This project implements a **real-time, multiplayer quiz game** where several players connect to a central server, answer timed networking questions, and compete on a live leaderboard. The twist: the **same game logic is built on two different transport protocols** so their behavior can be compared directly.

| Implementation | Transport | Concurrency Model | Client Interface |
| --- | --- | --- | --- |
| **`Project_TCP/`** | TCP (connection-oriented) | Thread-per-client | **Web UI** (HTML/CSS/JS) via an HTTP bridge |
| **`UDP_Project/`** | UDP (connectionless) | Single-socket event loop | **Terminal** (CLI) |

Both servers implement a custom **application-layer protocol** over raw sockets: JSON messages, time-based scoring, broadcast questions, per-question results, and live top-3 leaderboards — with no external frameworks. Everything runs on the **Python standard library only**.

This was developed as the **CS411 – Computer Networks** lab project (Lab 4) at the **Mediterranean Institute of Technology (MedTech)**.

---

## ✨ Key Features

- **Two complete transport-layer implementations** of the same game (TCP + UDP) for direct comparison.
- **Multi-threaded TCP server** handling many concurrent players with a dedicated thread per connection.
- **Thread-safe shared state** — all access to scores, answers, and the client registry is guarded by locks to prevent race conditions.
- **Custom JSON message protocol** with newline framing over the TCP byte stream, and datagram-based messaging over UDP.
- **Time-based scoring engine** — faster correct answers earn more points: `score = max(0, 100 − 3 × seconds)`.
- **Live leaderboards** broadcast after every question, plus a final ranking and winner announcement.
- **Web client for TCP** — a browser-based UI served by a lightweight HTTP bridge that translates HTTP requests into TCP socket messages.
- **Resilient UDP server** — address-based client tracking, heartbeat `ping`/`pong`, automatic cleanup of inactive clients, and graceful handling of malformed/dropped packets.
- **Auto IP discovery & LAN play** — the TCP server detects and prints its LAN IP so players on other machines can connect.
- **Zero external dependencies** — pure standard-library Python.

---

## 🧠 Why This Project Matters (Skills Demonstrated)

This project goes beyond using a web framework — it implements the networking layer by hand, which demonstrates:

- **Socket programming** with the raw BSD socket API (`AF_INET`, `SOCK_STREAM`, `SOCK_DGRAM`).
- **Transport-protocol fluency** — understanding *and engineering around* the practical differences between TCP and UDP (reliability, ordering, framing, connection state).
- **Concurrency & thread safety** — thread-per-client design, `threading.Lock`, and reasoning about shared mutable state.
- **Protocol design** — defining a clean application-layer message schema and a framing strategy (newline-delimited JSON) on top of a raw byte stream.
- **Client-server architecture** — separation of game logic, transport, and presentation layers.
- **Full-stack reach** — Python backend + an HTML/CSS/JavaScript front end bridged to sockets over HTTP.
- **Engineering trade-off analysis** — empirically comparing protocols and reasoning about which fits which workload.

---

## 🏗️ Architecture

### TCP Architecture (web client)

```
┌──────────────────────┐      TCP socket (port 8888)      ┌──────────────────────┐
│   TCP Game Server     │◄────────────────────────────────►│    Client Bridge      │
│   server_tcp.py       │   newline-delimited JSON stream   │    client_tcp.py      │
│                       │                                   │                       │
│ • Thread-per-client   │                                   │ • TCP socket client   │
│ • Game loop & timing  │                                   │ • HTTP server (:8000) │
│ • Scoring engine      │                                   │ • Async message queue │
│ • Leaderboards        │                                   │                       │
│ • Lock-guarded state  │                                   └───────────▲───────────┘
└──────────────────────┘                                               │
                                                              HTTP / JSON (port 8000)
                                                                        │
                                                            ┌───────────┴───────────┐
                                                            │     Web Interface      │
                                                            │  index.html / JS / CSS │
                                                            │  • Polls for messages  │
                                                            │  • Renders questions   │
                                                            │  • Live leaderboard    │
                                                            └────────────────────────┘
```

The browser never speaks raw TCP. Instead, the **client bridge** maintains the TCP connection to the game server and exposes a tiny HTTP API (`/api/connect`, `/api/answer`, `/api/messages`) that the JavaScript front end polls — effectively a hand-rolled TCP-to-HTTP gateway.

### UDP Architecture (terminal clients)

```
┌──────────────────────┐                          ┌────────────────────┐
│   UDP Game Server     │   UDP datagrams (8888)   │   Terminal Client  │
│   server_udp.py       │◄────────────────────────►│   client_udp.py    │
│                       │                          │                    │
│ • Single UDP socket   │      ┌───────────────────┤  • Direct UDP I/O  │
│ • Address→player map   │◄─────┤   Terminal Client │  • Listener thread │
│ • Heartbeat ping/pong │      │   client_udp.py   │  • Timed input     │
│ • Inactivity cleanup  │      └────────────────────┘                   │
│ • Best-effort delivery│                                               │
└──────────────────────┘                                               │
```

One socket multiplexes *all* clients; the server distinguishes players by their `(IP, port)` source address rather than by a persistent connection.

---

## ⚖️ TCP vs. UDP — The Core Comparison

The whole point of building it twice was to feel the differences in practice:

| Concept | TCP Implementation | UDP Implementation |
| --- | --- | --- |
| **Connection** | Three-way handshake; persistent socket per client | Connectionless; no handshake, datagrams only |
| **Reliability** | Guaranteed, in-order delivery (built in) | Best-effort; loss is possible and must be tolerated |
| **Message framing** | Byte stream → manual newline (`\n`) delimiting | Self-contained datagrams (one message per packet) |
| **Client tracking** | Automatic via the live connection | Manual: server maps `(ip, port)` → player |
| **Liveness** | Socket close detected automatically | Heartbeat `ping`/`pong` + inactivity timeout |
| **Concurrency** | Thread-per-client | Single socket, single receive loop |
| **Overhead** | Higher (per-connection state, ACKs) | Lower (no connection state) |
| **Best for** | Quiz/trivia, finance, file transfer — integrity matters | Action games, VoIP, streaming — latency matters |

**Takeaway:** for a quiz game, **TCP is the better fit** — losing a question or an answer would corrupt the game state — while UDP shines when occasional loss is acceptable in exchange for lower latency. The right protocol depends on the application's tolerance for loss vs. its need for speed.

---

## 🧮 Scoring & Game Flow

**Scoring formula** (identical across both protocols):

```python
score = max(0, 100 - 3 * seconds_taken)   # correct answers only; wrong/late = 0
```

| Response time | Points (if correct) |
| --- | --- |
| 2 s | 94 |
| 5 s | 85 |
| 10 s | 70 |
| 20 s | 40 |
| 30 s+ | ~10 |
| Wrong answer | 0 |

**Game loop:**

1. **Join phase** — players connect and register a username; the host starts the game manually.
2. **Question phase** — the server broadcasts each question; a 30-second timer runs and ends early once everyone has answered.
3. **Result phase** — the server scores each answer, sends individual results, and broadcasts the top-3 leaderboard.
4. **End phase** — final standings are shown and the winner is announced.

---

## 📡 Application-Layer Message Protocol

Messages are JSON objects. Over TCP they are newline-framed on the stream; over UDP each message is a single datagram.

**Client → Server**

```json
{ "type": "join",   "username": "Ahmed" }
{ "type": "answer", "question_id": 1, "answer": "B", "time": 2.3 }
```

**Server → Client**

```json
{ "type": "question", "id": 1, "number": 1, "text": "What does TCP stand for?",
  "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "timeout": 30 }

{ "type": "result", "correct": "B", "your_answer": "B",
  "is_correct": true, "points": 94, "total_score": 94 }

{ "type": "leaderboard", "top3": [{ "u": "Ali", "s": 250 }, { "u": "Ahmed", "s": 180 }] }

{ "type": "end", "leaderboard": [ ... ], "winner": "Ali" }
```

---

## 🛠️ Tech Stack

- **Language:** Python 3.7+
- **Networking:** `socket` (TCP & UDP), `http.server`, `socketserver`
- **Concurrency:** `threading`, `threading.Lock`
- **Data / protocol:** `json`, UTF-8, custom newline framing
- **Front end (TCP):** HTML5, CSS3, vanilla JavaScript (fetch + polling)
- **Dependencies:** none beyond the standard library

---

## 📂 Repository Structure

```
project_TCP-UDP/
├── Project_TCP/                # TCP implementation (web client)
│   ├── server_tcp.py           # Multi-threaded TCP game server
│   ├── client_tcp.py           # TCP↔HTTP bridge + static web server
│   ├── web/
│   │   ├── index.html          # Player UI (login, question, leaderboard)
│   │   ├── style.css           # Responsive gradient design
│   │   └── script.js           # Game state + live polling
│   ├── data/questions.json     # Quiz question bank
│   ├── utils/messages.py       # JSON encode/decode + framing helpers
│   ├── requirements.txt
│   ├── ARCHITECTURE.md         # Deep-dive architecture notes
│   └── README.md
│
├── UDP_Project/                # UDP implementation (terminal clients)
│   ├── server_udp.py           # Single-socket UDP game server
│   ├── client_udp.py           # Terminal client
│   └── questions.json
│
├── NetWorks_Lab4.pdf           # Full lab report (design + TCP/UDP analysis)
└── Project_Presentation.pdf    # Project presentation slides
```

---

## 🚀 Getting Started

> Requires **Python 3.7+**. No installation needed — only the standard library is used.

### Run the TCP version (web client)

**1. Start the server** (terminal 1):

```bash
cd Project_TCP
python server_tcp.py
```

The server prints its LAN IP and waits for players. Type `start` and press Enter to begin; type `next` to advance between questions.

**2. Start a client bridge** (terminal 2) — this also opens the web UI in your browser:

```bash
# same machine as the server
python client_tcp.py

# or connect across the LAN (use the IP the server printed)
python client_tcp.py 192.168.1.100
```

Then enter a username in the browser and play. Run multiple client bridges (the web port auto-increments) to add more players.

### Run the UDP version (terminal client)

**1. Start the server:**

```bash
cd UDP_Project
python server_udp.py
```

**2. Start one or more clients:**

```bash
python client_udp.py            # localhost
python client_udp.py 192.168.1.100   # across the LAN
```

Enter a username, then type `start` in the server terminal to begin.

---

## 🧩 Engineering Challenges & Solutions

- **Message framing over a TCP stream.** TCP delivers a continuous byte stream with no message boundaries, so two JSON messages can arrive glued together or split apart. *Solution:* newline-delimited framing with a per-connection buffer that extracts complete messages and retains partial ones.
- **Concurrency & race conditions.** Many client threads read and mutate shared scores and answers simultaneously. *Solution:* a single `threading.Lock` guards every critical section (registry, answers, scoring, broadcasts).
- **Bridging a browser to raw TCP.** Browsers can't open arbitrary TCP sockets. *Solution:* a lightweight HTTP bridge that holds the TCP connection and exposes a minimal polling API the JavaScript front end consumes.
- **Liveness without connections (UDP).** UDP has no concept of a dropped connection. *Solution:* track each client's last-seen timestamp via `ping`/`pong` heartbeats and prune clients that exceed an inactivity timeout.

---

## 🔭 Possible Future Enhancements

- Replace HTTP polling with **WebSockets** for true push-based real-time updates.
- Add **application-level acknowledgments and retransmission** to the UDP version for reliable delivery without TCP.
- Explore a **QUIC**-based version combining UDP's speed with TCP-like reliability.
- Add automated **load/latency benchmarking** and a metrics dashboard.
- Containerize with **Docker** for reproducible multi-client demos.

---

## 👥 Authors & Roles

This was a team project for **CS411 – Computer Networks (Lab 4)** at the **Mediterranean Institute of Technology (MedTech)**, supervised by **Mr. Iheb Hergli**.

| Member | Role | Focus |
| --- | --- | --- |
| **Ahmed Hamouda** | **System Architect** | TCP server core, threading model, game-state management, performance optimization |
| Aymen Saad | Frontend Engineer | Web interface, JavaScript client, real-time UI/UX |
| Yassine Mtibaa | Protocol Engineer | UDP implementation, message reliability, network testing |
| Youssef Benmoussa | Quality Assurance | Testing, documentation, performance benchmarking |

---

## 📄 License

Released for educational purposes. Feel free to fork, study, and build on it.

---

<p align="center"><i>Built to understand transport protocols by implementing them — not just reading about them.</i></p>
