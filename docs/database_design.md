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
- `events`: authoritative append-only history with `previous_hash` and unique
  `event_hash` chain links.
- `terminals`: reserved terminal registration data for future authentication.

## Transaction Ownership

Repositories execute SQL and never commit. `UnitOfWork` creates the repositories,
opens `BEGIN IMMEDIATE`, and performs the single commit or rollback. Services use
a fresh Unit of Work for each operation. No repository calls another repository,
and transport code never accesses SQLite directly.

## Event Integrity

For canonical event data `E(n)` and the preceding hash `H(n-1)`:

```text
H(n) = SHA256(canonical_json(H(n-1), E(n)))
```

The first event references a fixed genesis hash. Existing version-1 event rows
are retained and backfilled by migration version 2.
