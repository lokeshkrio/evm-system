# EVM-System-v2 Architecture

This document is the source of truth for the current backend architecture. The
README is an overview; when the two differ, this document takes precedence.

## Layering

Requests flow through these layers:

```text
WebSocketServer -> RPCDispatcher -> ElectionService -> Repositories -> SQLite
                                      |                  |
                                      v                  v
                               StateMachine       database events
                                      |
                                      v
                              JSONL audit mirror
```

- `server/` owns WebSocket and JSON-RPC behavior. It contains no election rules or SQL.
- `services/` coordinates use cases and transaction boundaries. It contains no SQL.
- `repositories/` owns SQL for one persistence concern per repository.
- `database/` owns connection lifecycle, transactions, schema creation, and migrations.
- `models/` owns domain data structures and enums.
- `clients/` owns client-side communication and presentation.

## Election Lifecycle

```text
INITIALIZED -> STARTED -> VOTING -> STARTED
                            |
                            v
                          HALTED -> STARTED

STARTED or HALTED -> ENDED
```

Transitions are explicit: `start_election()`, `enable_vote()`, `vote_casted()`,
`halt()`, `resume()`, and `end()`. `VOTING` grants one voting opportunity. A
successful vote automatically returns the state to `STARTED`.

All mutating election operations share one `asyncio.Lock`. This prevents an
administrative transition from interleaving with a vote while database I/O is
in progress.

## Persistence and Transactions

`ElectionService` coordinates transactions but delegates each SQL statement to
the repository that owns its table. A successful vote transaction contains:

1. insertion into `votes`;
2. persistence of the resulting `STARTED` state in `metadata`;
3. insertion of the `VOTE_CAST` record into `events`.

The three writes commit or roll back together. Lifecycle transitions similarly
persist metadata and their database event together. Runtime state is restored
to its previous value when persistence fails.

The database `events` table is the authoritative operational event history.
`logs/audit_ledger.jsonl` is a hash-chained secondary mirror. Failure of that
secondary sink is logged but does not report a committed operation as failed.

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
