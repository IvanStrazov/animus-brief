# animus-brief

[![tests](https://github.com/IvanStrazov/animus-brief/actions/workflows/test.yml/badge.svg)](https://github.com/IvanStrazov/animus-brief/actions/workflows/test.yml)
[![version](https://img.shields.io/badge/version-0.1.0-blue)](CHANGELOG.md)
[![license: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
![dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen)
![python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)

**"What was I doing?" — answered across all your projects in one short brief.**

> **Part of Animus** — small, local, token-frugal plugins that let Claude Code remember you and your work. Each works alone; together they share context through `~/.claude/ecosystem.json`.
>
> | Plugin | What it does |
> |---|---|
> | [animus-journal](https://github.com/IvanStrazov/animus-journal) | Project journal on a hard token budget: what was done, decided, next |
> | [animus-portrait](https://github.com/IvanStrazov/animus-portrait) | A compact portrait of you, built from your own sessions |
> | [animus-brief](https://github.com/IvanStrazov/animus-brief) | One status brief across all your projects |
> | [animus-limits](https://github.com/IvanStrazov/animus-limits) | Token spend per task, per-task limits, cost estimates |
> | [animus-relay](https://github.com/IvanStrazov/animus-relay) | Hand work over to a fresh session without losing the thread |
> | [animus-review](https://github.com/IvanStrazov/animus-review) | Send work to another model for review, triage the answer |
>
> The name nods to the memory machine from Assassin's Creed and to the Latin *animus*, "mind". Not affiliated with Ubisoft.

## Install

```
/plugin marketplace add IvanStrazov/animus-brief
/plugin install animus-brief@animus-brief
```

Then say `/brief`. Requires Python 3.9+ on `PATH` (`python3` or `python`); works on macOS, Linux and Windows (Git Bash).

## What you get

Say `/brief`, "what's the status" or "what was I doing". Claude runs one script and answers in ~15 lines:

- **Now** — the most recent threads, each with its concrete next step
- **Stale** — projects untouched for a week (configurable)
- **Waiting on you** — next steps that need your decision or action
- **Limits** — warnings from [animus-limits](https://github.com/IvanStrazov/animus-limits), if installed

It reads [animus-journal](https://github.com/IvanStrazov/animus-journal) journals: the global `~/journal` (one line per topic, superseded topics hidden) and every `<project>/.journal` of projects seen in your Claude Code transcripts. Project `STATE.md` lines (*In progress*, *Next steps*, *Open questions*) win over entry `Next:` lines.

## Token budget

| Moment | Cost |
|---|---|
| Session start | nothing — no hooks |
| `/brief` | script output ≤ 40 lines (`--max-lines`) + ~1 KB of skill instructions |

## Commands

```
brief.py show [--days 30] [--stale 7] [--max-lines 40]
brief.py where        # journals found
```

## Privacy

Everything stays on your machine: plain Markdown and JSON files, no network, no database, one stdlib Python script.

## License

MIT
