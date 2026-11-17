---
name: brief
description: One compact status brief across all projects, from animus-journal — what each project is doing, next steps, what went stale, and token-limit warnings. Use on /brief, "what's the status", "what was I doing", "what's pending", "brief me", or at the start of a day.
---

# Brief

`B` = `python3 "<plugin root>/scripts/brief.py"`, where the plugin root is two levels above this skill's base directory. Use `python` if `python3` is missing (Windows). The script reads the journals itself; never open journal files for this.

1. Run `B show` (options: `--days N` for the activity window, default 30; `--stale N`, default 7 days).
2. Answer in the user's language, in this shape, at most ~15 lines:
   - **Now:** the 2–3 most recent threads, one line each, with the concrete next step.
   - **Stale:** projects marked STALE and the `Dormant` line (no entry within the window), one line each, only if any.
   - **Waiting on you:** next steps that need the user (an approval, an account, a decision), if any.
   - **Limits:** the `[limits]` lines, if the script printed any.
3. End with one question: which thread to pick up. Do not start work on it before the user answers.

Projects come from Claude Code transcripts plus the current folder. To drop an abandoned project from the brief: `B hide <name>` (`B unhide <name>` to bring it back); its journal stays untouched. `B where` lists the journals scanned.
If the script finds no journals, say that the brief needs animus-journal entries and offer to record the current work.
