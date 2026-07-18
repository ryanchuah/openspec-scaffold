# roll-decisions-index follow-ons (shipped 2026-07-17)

See `knowledge/decisions/INDEX.md` (`roll-decisions-index`) for the shipped decision.
Neither item below gates other work.

1. **Pointer-line insertion position.** `_insert_pointer_line` inserts the pointer line after the
   FIRST `---` header separator, not the LAST/"closing" one as `tasks.md` phrased it. Indistinguishable
   on every current repo's single-`---` header; only diverges on a hypothetical multi-`---`/
   front-matter-style INDEX header. Harden to target the last separator if a repo ever adopts such a
   header — cosmetic until then.
2. **Budget/threshold tuning.** Cross-reference only — do not duplicate: the 16,000/12,000-byte
   defaults are judgment calls, tracked as item 2 of
   `knowledge/questions/knowledge-surface-bounding-2-follow-ons.md`.
