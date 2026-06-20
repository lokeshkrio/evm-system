# Database Design

SQLite runs with WAL mode and foreign-key enforcement enabled. Schema changes are
applied through ordered migrations after idempotent schema initialization.

## Tables

- `candidates`: candidate identity, party, and active status.
- `voters`: seed/demo voter data. Ballots do not store these raw identifiers.
- `votes`: one row per ballot; `voter_hash` is unique and `candidate_id` references
  `candidates` with restricted deletion.
- `metadata`: durable key/value data, including `election_state` and
  `schema_version`.
- `events`: authoritative append-only operational event history.
- `terminals`: reserved terminal registration data for future authentication.

## Transaction Ownership

Repositories execute SQL and accept caller-controlled commit behavior. Services
open transactions when a use case spans multiple repositories. No repository
calls another repository, and transport code never accesses SQLite directly.
