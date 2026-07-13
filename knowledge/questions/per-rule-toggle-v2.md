# Per-rule enable/disable toggle (v2)

From `openspec/changes/archive/2026-07-13-defect-prevention-detectors/notes.md` (assumption A3):

The two noise-prone `test-quality` rules (`unfrozen-clock`, `discarded-return-flag`) ship enabled but advisory-labeled in v1. A repo drowning in them must today disable the entire detector via `[checks.test-quality] enabled = false`, losing the four high-signal rules. A per-rule `disabled_rules = ["unfrozen-clock", "discarded-return-flag"]` config toggle — so high-signal rules stay on while noisy ones are silenced — is the real long-term fix.

**Deferral:** v2, observed from downstream adoption noise first. Do not build the toggle until at least one downstream repo reports real false-positive volume that makes the whole-detector toggle too coarse.

**Status:** parked — not blocking, revisit when downstream adoption noise warrants it.
