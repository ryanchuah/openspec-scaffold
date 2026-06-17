# Explore brief — fix-convergence-guard (W3)

MEDIUM tier. Full exploration record is the workflow audit; this brief is the
cold-start anchor (R2 💡#4).

## Sources of truth
- `ai-docs/workflow-audit-2026-06-16.md` §A1–A5 — the findings being fixed.
- `ai-docs/consolidation-plan-2026-06-16.md` — W3 row (ledger lines 166–170);
  apply order W0→W1→W2→{W3,W4,W5}→W6.

## Verified-on-disk anchors (re-checked this session)
| Finding | Anchor | What's there |
|---------|--------|--------------|
| A1 | `scripts/_convergence.py:197` | rule (a) fires only on *consecutive* signature match; `attempts` (`:192`) is never an independent cap |
| A2 | `scripts/_convergence.py:271` | signature computed over the WHOLE stdin |
| A2 | `scripts/_convergence.py:185,:264` | raw `test_id` used as state key (no normalization) |
| A4 | `scripts/_convergence.py:101` | greedy `re.sub(r'/\S+', ' <PATH> ', text)` runs first |
| A5 | `scripts/test-gate.sh:21-22` | `SCRIPT_DIR` absolute (good); `:41,49` resolve `command -v`/`$CMD` relative to cwd |
| spec | `openspec/specs/apply-convergence-guard/spec.md:23-24,31-34` | rule-(b) "about to edit" + "Healthy iteration is not interrupted" scenarios (both constrain the A1/A3 fixes) |
| tests | `scripts/test_convergence.py` | stdlib unittest (no pytest); existing normalize + rule-a/b coverage |

## Constraints carried into the design
- All five files are already in `scripts/scaffold_manifest.txt` → **not**
  manifest-changing; content edits only.
- Correctness fixes, not redesign: a/b/c trigger taxonomy, state-file layout,
  and executor protocol unchanged.
- The spec's "Healthy iteration" scenario forbids interrupting different-signature
  progress → A1 cannot be a blunt attempt cap (drove the oscillation-detection +
  high-backstop design).
