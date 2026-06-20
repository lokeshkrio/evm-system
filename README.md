# EVM-System-v2

A secure, asynchronous, event-driven Electronic Voting Machine backend built in Python. The project simulates the core components of a distributed voting system with append-only storage, cryptographic audit logs, JSON-RPC communication, and WebSocket-based clients.

## Overview

EVM-System-v2 is a learning and portfolio project designed to explore backend architecture, distributed systems, asynchronous programming, and secure event logging.

The system separates concerns into multiple layers:

- Network Layer
- Service Layer
- Repository Layer
- Database Layer
- Audit Layer

Communication between clients and the server is performed through JSON-RPC over WebSockets.

---

## Features

### Election Lifecycle

- Start election
- Stop election
- Halt election
- Query election status
- Query election state

### Voting

- Cast vote
- Duplicate vote prevention
- Candidate validation
- Voting state validation

### Audit Logging

- Append-only cryptographic ledger
- Hash-chained events
- Election start events
- Election stop events
- Halt events
- Vote events
- Duplicate vote events

### Network Layer

- JSON-RPC 2.0 protocol
- WebSocket server
- Multi-client support
- Connection management
- Request validation with Pydantic

### Persistence

- SQLite database
- Repository pattern
- Metadata storage
- Event storage
- Vote storage
- Candidate storage

### Architecture

- Layered architecture
- Dependency separation
- State machine driven workflow
- Async I/O using asyncio
- Repository pattern
- Service-oriented design

---

## Project Structure

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

## Architecture

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

## Technology Stack

- Python 3.13+
- asyncio
- websockets
- Pydantic
- SQLite
- aiosqlite
- JSON-RPC 2.0

---

## Design Principles

- Separation of concerns
- Append-only event storage
- Immutable audit ledger
- Asynchronous architecture
- Repository pattern
- Service layer abstraction
- Strong protocol validation

---

## JSON-RPC 2.0 Protocol Specifications

To ensure reliable and secure client-server communication, the system implements standard JSON-RPC 2.0 with custom features:

- **Unified Request Identification**: Transaction IDs (`id`) support both string and integer formats. The client generates unique IDs consisting of a `UUIDv4` token combined with a connection-specific host/port salt (`uuid4_host_port`) to prevent request collisions and track sessions.
- **Cryptographic Voter Anonymity**: Voter IDs are cryptographically hashed using SHA-256 on the client side (`voter_hash`) before transmission to the voting server to preserve voter anonymity in the database.
- **Strict Validation Schema**: All RPC methods and data payloads are validated using Pydantic models on both the sender and receiver sides.

---

## Future Improvements

- Event bus
- Publish-subscribe notifications
- HMAC request signatures
- Rate limiting
- Authentication
- Role-based access control
- Distributed nodes
- Leader election
- Persistent event sourcing
- Web dashboard
- Metrics and monitoring
- Unit and integration tests

---

## Learning Objectives

This project was built to explore:

- Async programming in Python
- WebSocket communication
- JSON-RPC protocol design
- State machines
- Repository pattern
- Service-oriented architecture
- Cryptographic audit logging
- Distributed systems concepts
- Backend engineering principles
- Event-driven design

---

## Disclaimer

This project is intended for educational purposes and is not designed for production elections.
