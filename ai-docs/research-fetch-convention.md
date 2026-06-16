# Research Fetch Convention

Standard block to paste into research-subagent prompts. Established 2026-06-03.

These conventions were measured to cut tokens substantially on article pages and
GitHub HTML vs raw, justifying the approaches below.

---

## Four rules for efficient web research

**(a) GitHub files — always fetch raw, never clone.**
For any GitHub repo or file, fetch via `raw.githubusercontent.com` directly or run
`python scripts/fetch_clean.py <github-url>` (it rewrites GitHub URLs to raw automatically).
**Do NOT `git clone` whole repos or `Read` many repo files** — pull only the specific
README or source file you need.

**(b) Full-page article content — use `fetch_clean` or targeted WebFetch.**
When you need the full cleaned text of a page, prefer:
```
python scripts/fetch_clean.py <url>
```
Use the built-in `WebFetch` tool with a *specific extraction prompt* when you only need a
targeted answer from the page (it summarizes server-side and is cheap for that use case).
Avoid loading whole raw HTML pages into context.

**(c) Be targeted — don't fetch what you won't cite.**
Only fetch a page if you will actually use and cite its content in the output.
Checkpoint to the output file as you go (write partial findings early; don't hold everything
in context until the end).

**(d) Never call the built-in `WebSearch` tool from the main thread.** Route ALL web research
through subagents that use `scripts/fetch_clean.py` (discover via a fetched search URL, then
fetch the chosen pages). This keeps the orchestrator context clean and lets research run in
parallel and checkpoint to disk; the orchestrator applies its own judgment to subagent reports.
