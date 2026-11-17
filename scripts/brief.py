#!/usr/bin/env python3
"""animus-brief: one compact status brief across all your projects, from animus-journal.

Finds every journal (the global ~/journal plus <project>/.journal for each project seen
in Claude Code transcripts), and prints per project: last activity, what is in progress,
the next steps, and whether it has gone stale. Topics in the global journal are listed
by their first tag. If animus-limits is installed, its warnings are appended.

Commands:
  show [--days N] [--stale N] [--max-lines N]   the brief (default: active in 30 days, stale after 7)
  where                                          list the journals found

Standard library only, Python 3.9+. No network.
"""
import argparse
import datetime as dt
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude").expanduser()
JOURNAL_GLOBAL = Path(os.environ.get("JOURNAL_GLOBAL_DIR") or Path.home() / "journal").expanduser()
ECO_FILE = Path(os.environ.get("CLAUDE_ECOSYSTEM_FILE") or CLAUDE_DIR / "ecosystem.json").expanduser()
SCRIPT = Path(__file__).resolve()
SELF = "animus-brief"
ENTRY_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+(.*?)\s+—\s+(.*)$")
STATE_KEYS = ("in progress", "next", "open questions", "blocked", "в работе", "дальше", "следующ")

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def journal_dir(cwd):
    """Same rule as animus-journal: git root/.journal, or the global dir for projectless sessions."""
    p = Path(cwd)
    s = str(p).replace("\\", "/").lower()
    if "scratch-workspaces" in s or not p.exists():
        return JOURNAL_GLOBAL
    for base in (Path.home(), Path(tempfile.gettempdir())):
        try:
            if p.resolve() == base.resolve():
                return JOURNAL_GLOBAL
        except OSError:
            pass
    try:
        top = subprocess.run(["git", "-C", str(p), "rev-parse", "--show-toplevel"], capture_output=True,
                             text=True, encoding="utf-8", errors="replace", timeout=5).stdout.strip()
    except Exception:
        top = ""
    return Path(top or p) / ".journal"


def known_cwds():
    root = CLAUDE_DIR / "projects"
    cwds = set()
    for f in root.glob("*/*.jsonl") if root.is_dir() else []:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh):
                    if '"cwd"' in line:
                        try:
                            cwds.add(json.loads(line)["cwd"])
                            break
                        except (ValueError, KeyError):
                            pass
                    if i > 50:
                        break
        except OSError:
            pass
    return cwds


def journals():
    seen, out = set(), []
    for d in [JOURNAL_GLOBAL] + sorted({journal_dir(c) for c in known_cwds()}, key=str):
        k = str(d).lower()
        if k not in seen and (d / "INDEX.md").is_file():
            seen.add(k)
            out.append(d)
    return out


def entries(jdir):
    out, cur = [], None
    for log in sorted((jdir / "log").glob("*.md")) if (jdir / "log").is_dir() else []:
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            m = ENTRY_RE.match(line)
            if m:
                tags = re.findall(r"#([^\s#]+)", m.group(2))
                cur = {"when": dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M"),
                       "tag": tags[0] if tags else "untagged", "tags": tags or ["untagged"],
                       "title": m.group(3), "next": []}
                out.append(cur)
            elif cur and re.match(r"^\s*(Next|Дальше)\s*:", line, re.I):
                cur["next"].append(line.split(":", 1)[1].strip())
    out.sort(key=lambda e: e["when"])
    return out


def state_lines(jdir):
    try:
        text = (jdir / "STATE.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    out = []
    for line in text.splitlines():
        low = line.strip().lower().lstrip("-* ")
        if any(low.startswith(k) for k in STATE_KEYS) and ":" in line and line.split(":", 1)[1].strip():
            out.append(line.strip().lstrip("-* "))
    return out


def clip(s, n=160):
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def ago(when, now):
    d = (now - when).days
    return "today" if d == 0 else ("yesterday" if d == 1 else f"{d}d ago")


def limits_lines():
    try:
        e = json.loads(ECO_FILE.read_text(encoding="utf-8"))
        cmd = e.get("plugins", {}).get("animus-limits", {}).get("cmd")
        if not cmd:
            return []
        # non-POSIX split keeps Windows backslashes but also keeps the quotes: strip them
        argv = [t[1:-1] if len(t) > 1 and t[0] == t[-1] == '"' else t
                for t in shlex.split(cmd, posix=os.name != "nt")]
        r = subprocess.run(argv + ["check"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60)
        return [l for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def register():
    try:
        e = json.loads(ECO_FILE.read_text(encoding="utf-8"))
        if not isinstance(e, dict):
            e = {}
    except (OSError, ValueError):
        e = {}
    e.setdefault("plugins", {})
    me = {"cmd": f'"{sys.executable}" "{SCRIPT}"'}
    if e["plugins"].get(SELF) != me:
        e["plugins"][SELF] = me
        try:
            ECO_FILE.parent.mkdir(parents=True, exist_ok=True)
            ECO_FILE.write_text(json.dumps(e, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass


def cmd_show(a):
    register()
    now = dt.datetime.now()
    blocks = []
    for j in journals():
        es = [e for e in entries(j) if (now - e["when"]).days <= a.days]
        if not es:
            continue
        if j == JOURNAL_GLOBAL:  # one block per topic (first tag), skipping topics a newer entry covers
            by_tag = {}
            for e in es:
                by_tag[e["tag"]] = e
            latest = sorted(by_tag.values(), key=lambda e: e["when"], reverse=True)
            for i, e in enumerate(latest):
                if any(set(e["tags"]) <= set(n["tags"]) for n in es if n["when"] > e["when"]):
                    continue
                blocks.append((e["when"], f"~/journal #{e['tag']}", e, []))
        else:
            blocks.append((es[-1]["when"], j.parent.name, es[-1], state_lines(j)))
    if not blocks:
        print(f"no journal activity in the last {a.days} days")
        return
    blocks.sort(key=lambda b: b[0], reverse=True)
    out = [f"Brief — {now:%Y-%m-%d}, {len(blocks)} active (last {a.days} days)"]
    for when, name, e, state in blocks:
        stale = " · STALE" if (now - when).days >= a.stale else ""
        out.append(f"■ {name} — {ago(when, now)}{stale}: {e['title']}")
        for s in state[:3]:
            out.append(f"   {clip(s)}")
        if not state:
            for n in e["next"][:2]:
                out.append(f"   Next: {clip(n)}")
    lim = limits_lines()
    if lim:
        out.append("Limits:")
        out += [f"   {l}" for l in lim]
    if len(out) > a.max_lines:
        cut = len(out) - a.max_lines + 1
        out = out[:a.max_lines - 1] + [f"(+{cut} lines; use --days or --max-lines)"]
    print("\n".join(out))


def cmd_where(_):
    for j in journals():
        print(j)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="brief.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("show")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--stale", type=int, default=7)
    p.add_argument("--max-lines", type=int, default=40)
    p.set_defaults(fn=cmd_show)
    sub.add_parser("where").set_defaults(fn=cmd_where)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
