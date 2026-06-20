# EVM-System-v2 Architecture

This document is the source of truth for the current backend architecture. The
README is an overview; when the two differ, this document takes precedence.

## Layering

Requests flow through these layers:

```text
Application
    |
    v
WebSocketServer -> RPCDispatcher -> ElectionService -> UnitOfWork -> SQLite
                                      |      |              |
                                      v      v              v
                             State policy  Repositories  chained events
                                             |
                                      post-commit EventBus
                                             |
                         Audit / Metrics / WebSocket subscribers
```

- `server/` owns WebSocket and JSON-RPC behavior. It contains no election rules or SQL.
- `services/` coordinates use cases through a Unit of Work. It contains no SQL.
- `repositories/` owns SQL for one persistence concern and never commits.
- `database/` owns connection lifecycle, Unit of Work, schema, and migrations.
- `events/` owns post-commit domain events, dispatch, and subscribers.
- `models/` owns domain data structures and enums.
- `clients/` owns client-side communication and presentation.
- `application.py` is the composition root and application lifecycle owner.

## Election Lifecycle

```text
INITIALIZED -> STARTED -> VOTING -> STARTED
                            |
                            v
                          HALTED -> STARTED

STARTED or HALTED -> ENDED
```

`metadata.election_state` is the source of truth. `ElectionStateMachine` stores
no state; it is a stateless policy exposing explicit `start_election()`,
`enable_vote()`, `vote_casted()`, `halt()`, `resume()`, and `end()` rules.
`VOTING` grants one voting opportunity. A successful vote atomically returns the
durable state to `STARTED`.

All mutating election operations share one `asyncio.Lock`. This prevents an
administrative transition from interleaving with a vote while database I/O is
in progress.

## Persistence and Transactions

`UnitOfWork` owns the transaction and commit. `ElectionService` coordinates the
use case while each repository owns its SQL. A vote transaction contains:

1. durable-state verification;
2. active-candidate verification;
3. duplicate-voter verification;
4. insertion into `votes`;
5. persistence of `STARTED` in `metadata`;
6. insertion of the chained `VOTE_CAST` record into `events`.

All checks and writes happen after `BEGIN IMMEDIATE` and commit or roll back
together. Lifecycle transitions similarly persist metadata and their event in
one Unit of Work.

Each database event stores `previous_hash` and `event_hash`. Startup verifies the
complete chain before serving requests. After commit, the domain event is
published to audit, metrics, and WebSocket subscribers. Subscriber failures are
logged and cannot change the committed result.

## Restart Recovery

The service restores `metadata.election_state` during startup. A persisted
`VOTING` state is recovered to `STARTED`: a process restart invalidates the
previous one-voter grant. The recovery is persisted and audited.

## Result Policy

Vote totals are unavailable until the election reaches `ENDED`. This prevents
live totals from influencing an election in progress.

## Current Security Boundary

Pydantic validates JSON-RPC envelopes and method parameters, including the
SHA-256 voter-hash format. SQLite enforces uniqueness and candidate references.
Transport authentication, authorization, HMAC replay protection, TLS deployment,
and rate limiting are not implemented yet and must not be described as active.
