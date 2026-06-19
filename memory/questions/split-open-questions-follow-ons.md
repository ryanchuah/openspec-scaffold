# split-open-questions follow-ons

Shipped 2026-06-17. Rationale in decisions registry; archive: `openspec/changes/archive/2026-06-17-split-open-questions/`.

- **Propagation to extrends + psc-monitor — DONE (2026-06-17).** `sync_scaffold.py` carried 4 managed files downstream; `--check` all IDENTICAL on both repos.
- **extrends `open-questions.md` one-time horizon split — DONE (extrends commit `4e46eb9`).** Split into active + parked via byte-integrity-gated `_open_questions_split_oneoff.py`; deepseek-v4-pro information-loss review READY, zero defects.
