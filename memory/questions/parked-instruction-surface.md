# Parked: instruction-surface

- **Redundant per-section summary paragraphs in legacy `open-questions.md` (LOW, overlaps C2/W7).** Each legacy section opens with a paragraph restating decisions/STATUS. New §3c archive rule stops authoring these; dropping existing ones pairs with migration cleanup. Originating change: `split-open-questions`.
- **config.yaml `rules:` block per-repo drift risk (LOW).** `openspec/config.yaml` `rules:` is per-repo and NOT manifest-synced; could drift between repos over time. Future hardening could sync via span-logic. Originating change: `single-source-rules`.
