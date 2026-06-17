## 1. AGENTS.md — read directive + horizon-split rule

- [x] 1.1 In the MANDATORY read blockquote at the top of `AGENTS.md`, add a new sentence to the blockquote **immediately after the sentence ending "…load a specific file there only when re-examining the closed decision it covers."** (i.e. as the next `>` line in that same blockquote paragraph). Insert exactly this sentence (preserving the leading `> ` blockquote marker to match the surrounding lines):

  `ai-docs/parked-follow-ons.md` is likewise NOT part of this mandatory read — it holds the deferred/monitored follow-on long tail grouped by `##` area; load only the relevant area section on demand when you start work in that area (`ai-docs/open-questions.md` stays read-in-full and bounded by the **open-questions.md horizon-split rule** — active items only).

  Do not change the `decisions.md` header-scan directive, the `STATUS.md`/`open-questions.md` "read in full" phrasing, or anything else in the blockquote.

- [x] 1.2 In `AGENTS.md` § "State, write discipline, and the archive-as-handoff rule", in the `**STATUS.md cap rule:**` paragraph, change its closing note. It currently reads: "Note that `open-questions.md` already prunes resolved items to `ai-docs/archive/retired-notes.md` and `decisions.md` is intentionally append-only." Replace with: "Note that `open-questions.md` is bounded by the **open-questions.md horizon-split rule** below (active items only; the deferred/monitored long tail parks to `ai-docs/parked-follow-ons.md`; resolved items still move to `ai-docs/archive/retired-notes.md`) and `decisions.md` is intentionally append-only."

- [x] 1.3 Immediately after the `**STATUS.md cap rule:**` paragraph (still inside the "Project-tracked docs — write-deferred…" bullet, same indentation), add a new sibling paragraph formatted exactly like the STATUS.md cap rule — a `**bold-led:**` paragraph at the same indentation, **not** a Markdown blockquote — encoding the **open-questions.md horizon-split rule**. The text below is authoritative; transcribe its substance and do not invent additional rules:

  **open-questions.md horizon-split rule:** `ai-docs/open-questions.md` is the always-loaded scan list and holds ONLY *active* items — open blockers (flagged **BLOCKING**), items needing an operator decision, and in-flight backlogs that gate other work. The deferred / monitored / low-priority long tail — follow-ons that only matter when the relevant area is next worked — lives in `ai-docs/parked-follow-ons.md` (grouped by `##` area headers; on-demand, NOT part of the mandatory onboarding read). Resolved items in either file move to `ai-docs/archive/retired-notes.md`. At archive the reconciliation routes each new follow-on to the correct file by horizon and keeps the active list lean. **A live blocker is never parked while it is live** — that is what preserves blocking-item visibility while bounding the always-loaded surface. The split is by horizon, never by age, so an old-but-live blocker is never demoted out of view.

- [x] 1.4 In `AGENTS.md` § "Working process", the bullet beginning "**Authored deliverables go only to the standard agent-neutral dirs**": change the `ai-docs/open-questions.md` parenthetical from "(open follow-ons)" to "(active open follow-ons / blockers)", and add a new listed item `ai-docs/parked-follow-ons.md` (deferred/monitored follow-ons) immediately after the open-questions.md item, so the quick-reference directory listing agrees with the horizon-split rule.

## 2. archive-executor bodies — horizon-routing reconciliation (§3c)

- [x] 2.1 In `.claude/agents/archive-executor.md`, replace the entire `#### 3c. Reconcile ai-docs/open-questions.md` subsection (its heading and its four bullets) with the routing version below. Write it as real Markdown in the same style as the rest of §3 — the fence here only delimits the content to write (do not emit the fence itself), and the descriptive paragraph between the `####` heading and the first bullet is intentional and must be kept:

  ```
  #### 3c. Reconcile `ai-docs/open-questions.md` and `ai-docs/parked-follow-ons.md`

  `ai-docs/open-questions.md` is the always-loaded scan list — it holds ONLY *active* items (open blockers, operator-decision items, in-flight backlogs that gate other work). The deferred / monitored / low-priority long tail lives in `ai-docs/parked-follow-ons.md` (grouped by `##` area headers; create it if absent), loaded on demand — not part of the mandatory onboarding read.

  - **Pull the open follow-ons** from notes.md's "Candidate open-questions / follow-ons for archive" section (if present), or from design.md's Risks / deferred Non-Goals, then **route each by horizon:**
    - *Active* — an open blocker, an item needing an operator decision, or an in-flight backlog that gates other work → append it to `ai-docs/open-questions.md`. Flag blockers with **BLOCKING**.
    - *Parked* — deferred, monitored ("watch and revisit if X recurs"), or low-priority cleanup that only matters when the relevant area is next worked → append it to `ai-docs/parked-follow-ons.md`, under the matching `##` area header (add one if none fits).
  - When this change produced active items, add a `## <topic> (shipped <date>)` section to `ai-docs/open-questions.md` opening with a one-line pointer to the full decision in `decisions.md` — do NOT restate the decision summary (that duplicates decisions.md/STATUS.md). Group parked items in `ai-docs/parked-follow-ons.md` under their area headers; a per-change pointer there is optional.
  - **A live blocker is never parked.** When unsure whether an item gates other work, keep it in `ai-docs/open-questions.md`.
  - **Resolved items** in either file move to `ai-docs/archive/retired-notes.md`. An active item that has clearly been deprioritized (no longer gating anything) may be moved to parked. Do NOT proactively re-classify the whole legacy file — route this change's new items and prune anything now resolved; bulk de-rotting of a pre-split file is a separate one-time migration.
  - Keep bullets lean in both files.
  ```

- [x] 2.2 Apply the **byte-identical** §3c replacement to `.opencode/agents/archive-executor.md` (same heading text, same bullets, same wording). The two bodies must match per the C4 guard — the only sanctioned divergence is the `.claude` intro clause "(the Claude Code counterpart of the OpenCode `@archive-executor`)", which §3c does not touch.

- [x] 2.3 Run `python3 scripts/test_executor_body_agreement.py` and confirm it passes (both executor pairs' bodies agree). If it fails on archive-executor, reconcile the two §3c edits until byte-identical.

## 3. Archive skill — verify-checklist assertion

- [x] 3.1 In `.claude/skills/openspec-archive-change/SKILL.md`, Step 6 ("Primary reviews, fixes, and commits") "Quality check" bullet list: replace the existing `ai-docs/open-questions.md` quality-check bullet (currently "- `ai-docs/open-questions.md` entry must list the open follow-ons from notes.md or design.md, with BLOCKING flags where appropriate.") with this exact bullet:

  - `ai-docs/open-questions.md` entry must contain ONLY active items (open follow-ons / blockers with **BLOCKING** flags where appropriate); deferred, monitored, or low-priority follow-ons must have been routed to `ai-docs/parked-follow-ons.md` under `##` area headers; and **no live blocker was parked**.

  Keep the existing `STATUS.md` ≤3-paragraph cap bullet (the one beginning "- `STATUS.md` retains at most **3** change paragraphs…") as-is.

## 4. parked-follow-ons.md home

- [x] 4.1 Create `ai-docs/parked-follow-ons.md` (per-repo state, NOT a scaffold-managed/manifest file — do **not** add it to `scripts/scaffold_manifest.txt`) with exactly this content:

  ```
  # Parked Follow-ons

  Deferred, monitored, and low-priority follow-ons — the long tail that only matters when you next
  work the relevant area. **Not part of the mandatory onboarding read** (see AGENTS.md): load the
  relevant `## ` area section on demand when you start work in that area. Live blockers and
  operator-decision items do NOT belong here — they live in `ai-docs/open-questions.md`. Resolved
  items move to `ai-docs/archive/retired-notes.md`.

  ---

  <!-- Group parked follow-ons under ## area headers (e.g. ## apply, ## verify, ## archive, ## sync).
       Each bullet: what's open, what gates it, and the originating change/archive pointer. -->
  ```

## 5. Guard suites stay green

- [x] 5.1 Run `python3 scripts/test_executor_body_agreement.py` and `python3 scripts/test_convergence.py`; confirm both pass (the executor-agreement guard is the load-bearing one for this change).
- [x] 5.2 Run `openspec validate --all` and confirm it passes (no spec deltas in this change; this confirms the live specs are unaffected).
