# JSON-RPC Protocol

The server accepts JSON-RPC 2.0 messages over WebSockets. Requests must contain
`jsonrpc: "2.0"`, a non-empty `method`, optional object `params`, and an optional
string or integer `id`. Messages without an ID are notifications and receive no
response.

## Methods

| Method | Parameters | Availability |
| --- | --- | --- |
| `start_election` | `{}` | `INITIALIZED` |
| `enable_vote` | `{}` | `STARTED` |
| `cast_vote` | `voter_hash`, `candidate_id` | `VOTING` |
| `halt_election` | `{}` | `VOTING` |
| `resume_election` | `{}` | `HALTED` |
| `stop_election` | `{}` | `STARTED` or `HALTED` |
| `get_state` | `{}` | always |
| `get_status` | `{}` | always |
| `get_results` | `{}` | totals only in `ENDED` |

`voter_hash` must be exactly 64 hexadecimal characters. `candidate_id` must be a
positive integer. Unknown or additional parameters are rejected.

## Errors

The server uses standard JSON-RPC error codes for parse errors, invalid requests,
unknown methods, invalid parameters, and internal errors. Internal exception
details are logged server-side and are not exposed to clients.
