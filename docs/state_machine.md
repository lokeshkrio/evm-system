# Election State Machine

| Current | Operation | Next | Meaning |
| --- | --- | --- | --- |
| `INITIALIZED` | `start_election` | `STARTED` | Election is active and waiting |
| `STARTED` | `enable_vote` | `VOTING` | One voter may submit a ballot |
| `VOTING` | successful `cast_vote` | `STARTED` | Grant is consumed |
| `VOTING` | `halt_election` | `HALTED` | Active voting is halted |
| `HALTED` | `resume_election` | `STARTED` | Election resumes in waiting state |
| `STARTED` | `stop_election` | `ENDED` | Election is finalized |
| `HALTED` | `stop_election` | `ENDED` | Halted election is finalized |

The state machine is stateless. Each method accepts the durable current state and
returns the permitted next state or `None`. `metadata.election_state` is always
the authoritative state.

Every other transition is rejected without changing persisted state.
On restart, persisted `VOTING` is deliberately recovered to `STARTED` because a
one-voter grant cannot safely survive loss of its client session.
