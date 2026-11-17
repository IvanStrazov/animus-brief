# Changelog

## 0.2.1 — 2026-11-17
- Skill: on Windows, take the interpreter from ecosystem.json when `python`/`python3` are Store stubs; forward slashes in paths.

## 0.2.0 — 2026-11-17
- The current folder's journal is always included, even before any transcript mentions it.
- Projects with no entry inside the window are listed on one `Dormant` line instead of vanishing.
- New `hide NAME` / `unhide NAME`: leave an abandoned project out of the brief; its journal is untouched (`where` marks hidden ones).

## 0.1.1 — 2026-11-17
- Fix: on Windows the Limits block was always empty — the quoted `cmd` from ecosystem.json kept its quotes and `limits check` never ran.

## 0.1.0 — 2026-11-17
- First release, part of the Animus ecosystem.
