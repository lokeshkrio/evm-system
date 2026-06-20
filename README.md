# EVM-System-v2

An asynchronous, event-driven Electronic Voting Machine backend written in Python. The system uses JSON-RPC over WebSockets, layered architecture, state machines, and append-only audit logs to simulate the backend components of a secure voting infrastructure.

> **Educational Project**
>
> This project is intended for learning backend engineering, asynchronous programming, networking, and system design concepts. It is **not intended for real-world elections**.

---

# Features

## Election Lifecycle

- Start election
- Enable one voting session
- Stop election
- Halt election
- Resume election
- Query election status
- State machine driven workflow

## Voting

- Cast votes
- Duplicate vote prevention
- Candidate validation
- Election state validation

## Audit Logging

- Append-only event storage
- Hash-chained events
- Startup event-chain verification
- Election start events
- Election stop events
- Halt events
- Vote events
- Duplicate vote attempts

## Networking

- JSON-RPC 2.0 protocol
- WebSocket communication
- Multi-client support
- Connection management
- Request validation using Pydantic

## Persistence

- SQLite database
- Repository pattern
- Candidate storage
- Vote storage
- Metadata storage
- Event storage

## Architecture

- Layered architecture
- State machine driven workflow
- Async I/O with asyncio
- Repository pattern
- Service layer abstraction
- Unit of Work transaction boundary
- Post-commit event bus
- Separation of concerns

---

# Technology Stack

- Python 3.13+
- asyncio
- websockets
- Pydantic
- SQLite
- aiosqlite
- JSON-RPC 2.0

---

# High-Level Architecture

```text
Client
    │
    ▼
WebSocket Server
    │
    ▼
RPC Dispatcher
    │
    ▼
Election Service
    │
 ┌──┴─────────────────┐
 ▼                    ▼
State Machine     Audit Service
 │
 ▼
Repositories
 │
 ▼
SQLite Database
```

---

# Core Components

| Component        | Responsibility       |
| ---------------- | -------------------- |
| WebSocket Server | Client communication |
| RPC Dispatcher   | Request routing      |
| Election Service | Business logic       |
| State Machine    | Election lifecycle   |
| Audit Service    | Event logging        |
| Repositories     | Data access layer    |
| SQLite           | Persistent storage   |

---

# Project Structure

```text
.
├── clients/
│   ├── admin/
│   ├── terminal/
│   └── base/
│
├── database/
│   ├── connection.py
│   ├── init_db.py
│   └── schema.sql
│
├── models/
│
├── repositories/
│   ├── vote_repository.py
│   ├── candidate_repository.py
│   ├── metadata_repository.py
│   └── event_repository.py
│
├── services/
│   ├── election_service.py
│   ├── state_machine.py
│   └── audit_service.py
│
├── server/
│   ├── websocket_server.py
│   ├── rpc_dispatcher.py
│   ├── connection_manager.py
│   └── protocol.py
│
├── tests/
├── logs/
├── data/
├── main.py
└── README.md
```

---

# Quick Start

## Clone Repository

```bash
git clone https://github.com/yourusername/EVM-System-v2.git
cd EVM-System-v2
```

## Create Virtual Environment

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

For local development tooling:

```bash
pip install -e ".[dev]"
```

## Initialize Database

```bash
python database/init_db.py
```

## Start Server

```bash
python main.py
```

---

# JSON-RPC Protocol

The system communicates using JSON-RPC 2.0 over WebSockets.

Supported methods are `start_election`, `enable_vote`, `cast_vote`,
`halt_election`, `resume_election`, `stop_election`, `get_state`, `get_status`,
and `get_results`. Vote totals are returned only after the election has ended.

## Example Request

```json
{
    "jsonrpc": "2.0",
    "method": "cast_vote",
    "params": {
        "voter_hash": "f4ab7d4f1c8e...",
        "candidate_id": 3
    },
    "id": "e8d47f32"
}
```

## Example Response

```json
{
    "jsonrpc": "2.0",
    "result": {
        "status": "success"
    },
    "id": "e8d47f32"
}
```

---

# Security Features

## Voter Anonymity

Voter identifiers are hashed using SHA-256 before transmission and storage.

## Validation

All requests are validated using Pydantic schemas.

## Duplicate Vote Prevention

The system prevents multiple votes from the same voter.

## Immutable Audit Trail

Events are stored in an append-only hash chain.

---

# Design Principles

- Separation of concerns
- Layered architecture
- Repository pattern
- Service-oriented design
- State machine driven workflow
- Immutable event storage
- Async architecture
- Strong protocol validation

---

# Sequence Flow

```text
Terminal Client
       │
       ▼
WebSocket Server
       │
       ▼
RPC Dispatcher
       │
       ▼
Election Service
       │
       ▼
Repositories
       │
       ▼
SQLite Database
```

---

# Planned Improvements

- HMAC request signatures
- Rate limiting
- Authentication
- Role-based access control
- Metrics and monitoring
- Integration tests
- Export functionality
- Candidate import from JSON

---

# Experimental Ideas

- Distributed nodes
- Leader election
- Event bus
- Publish-subscribe architecture
- Web dashboard
- Persistent event sourcing

---

# Learning Objectives

This project was built to explore:

- Async programming with asyncio
- WebSocket communication
- JSON-RPC protocol design
- State machines
- Repository pattern
- Service-oriented architecture
- Event-driven systems
- Secure audit logging
- Backend engineering principles
- Distributed systems concepts

---

# Disclaimer

This project is intended solely for educational purposes and portfolio development. It is not designed or certified for use in real-world elections.

---

# License

MIT License
