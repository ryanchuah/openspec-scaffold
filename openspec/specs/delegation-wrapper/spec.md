## Purpose

Six OpenSpec skills each used to hand-roll the identical post-processing after an `opencode run` delegation (fallback-grep, text extraction, marker assertion, EXIT-sentinel polling, exit-code interpretation), and nothing recorded what delegated runs actually do — so the "exit codes lie" lesson was re-learned every session and yield analysis was reconstructed from narrative review-logs. This capability makes the post-processing one deterministic, tested script and appends one line of telemetry per run to an untracked ledger, feeding the two scheduled evidence-gated decisions (premise-gate downgrade, MEDIUM pro-pass downgrade). It is distinct from `noninteractive-delegation-safety` (which governs the invocation's permission hardening — left untouched, since the invocation stays literal).

## Requirements

### Requirement: Delegated-run post-processing is performed by one deterministic tested wrapper
Delegated-run post-processing SHALL be performed by a single deterministic, tested script (`scripts/opencode_delegate.py`) rather than hand-rolled per skill. Given one completed `opencode run`'s stdout JSONL, stderr log, and exit code (as a literal for synchronous calls or via an EXIT-sentinel file for background calls), the wrapper SHALL detect silent agent fallback ("Falling back to default agent"), extract the completion text (the last `type:"text"` part), classify the run status (`ok`, `fallback`, `timeout`, `crash`, `truncated-stream`, or `marker-missing`), optionally assert one or more required marker regexes and capture an optional verdict token, and write the extracted text plus a machine-readable result. The wrapper SHALL NOT judge disk state (apply/archive/fix success is disk-judged by the orchestrator), SHALL NOT implement the failure ladder (retry, Sonnet fallback, git-checkpoint restore remain orchestrator judgment), and SHALL NOT gate any phase. Because delegated executors legitimately exit nonzero at session teardown on success, a nonzero-but-not-timeout exit accompanied by present completion text SHALL NOT be classified `crash`; `fallback` and a `timeout`/SIGKILL exit (124/137) are the hard operational-failure signals. Conversely, because a provider stream can return an empty completion that opencode accepts as a clean exit-0 end-of-stream, a run whose stdout JSONL shows more `step_start` than `step_finish` events (an unterminated final step) SHALL be classified `truncated-stream` — a distinct operational-failure signal caught on every phase regardless of whether a required marker was set — taking precedence over `marker-missing` but not over `fallback`, `timeout`, or a no-text `crash`. The skill's literal `timeout … opencode run … < /dev/null` invocation is unchanged, so this capability adds no requirement on, and does not weaken, the invocation hardening or the budget-agreement guard.

#### Scenario: The wrapper collapses the hand-rolled post-processing
- **WHEN** a skill completes an `opencode run` delegation and invokes the wrapper with the run's out/err/exit
- **THEN** the wrapper reports fallback, extracted text, status, and any verdict, and the skill performs no hand-rolled grep/jq/exit-code interpretation of its own

#### Scenario: The exit-code lie does not mask a successful run
- **WHEN** a delegated executor exits 1 at teardown but produced a complete non-empty completion text and no fallback occurred
- **THEN** the wrapper classifies the run `ok` (not `crash`) while still recording the raw exit code
- **AND** a `timeout`/SIGKILL exit (124/137) or a fallback is classified as an operational failure

#### Scenario: A silently-truncated stream is caught even without a required marker
- **WHEN** a delegated run exits 0 with partial completion text but its stdout JSONL ends with an unterminated step (`step_start` count exceeds `step_finish` count) and no required marker was set
- **THEN** the wrapper classifies the run `truncated-stream` (not `ok`) and exits nonzero, so the orchestrator's failure ladder fires

### Requirement: Each delegated run appends one telemetry line to an untracked ledger
Each delegated-run post-processing SHALL append exactly one JSON line to a delegation telemetry ledger at `output/delegation-log.jsonl` (untracked, append-only, created on demand), recording at minimum the timestamp, phase, agent, model, change identifier, exit code, fallback flag, classified status, marker-ok flag, verdict (when a verdict regex applied), and retry ordinal, plus any free-form tags supplied (e.g. the selected lens). The ledger is local operational telemetry that feeds scheduled evidence-gated decisions (the premise-gate downgrade at ~50 cumulative reviews and the MEDIUM pro-pass downgrade at ~20 verifies); it is not itself a gate, and the durable per-change record remains `review-log.md` / `notes.md`.

#### Scenario: A run is recorded once
- **WHEN** the wrapper post-processes a delegated run
- **THEN** exactly one JSON line carrying at least ts, phase, agent, model, change, exit, fallback, status, marker_ok, verdict, and retry is appended to `output/delegation-log.jsonl`
- **AND** the ledger accumulates across runs and sessions without truncating prior lines
