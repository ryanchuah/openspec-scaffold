# Parked: sync-mechanism

- **Sync guard `350` is a new magic number (LOW, monitor).** Propagating state-bounding rules pushed `extrends/AGENTS.md` 299→302 lines, tripping the 300-line tail-separator guard; bumped to 350. If synced span keeps growing, revisit or adopt explicit empty-tail convention. Originating change: `lean-boot-context`.
  - **Update (doc-scaffold-propagation):** the new `## Scaffold-managed files & propagation` section grew span2 again — `psc-monitor/AGENTS.md` is now 355 lines (safe: it has a tail appendix the guard anchors on), `extrends/AGENTS.md` 326 (no tail, ~24 lines of headroom to 350). The no-tail repos are the ones to watch; if extrends crosses 350 without a tail, sync aborts. Adopting the explicit empty-tail convention would retire the magic number.
