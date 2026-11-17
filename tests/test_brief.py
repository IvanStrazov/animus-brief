"""End-to-end tests for scripts/brief.py (stdlib unittest, no dependencies)."""
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "brief.py"


class BriefTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.claude = self.tmp / "claude"
        self.glob = self.tmp / "journal"
        self.proj = self.tmp / "work" / "bot"
        self.proj.mkdir(parents=True)
        self.env = dict(os.environ, CLAUDE_CONFIG_DIR=str(self.claude), JOURNAL_GLOBAL_DIR=str(self.glob),
                        CLAUDE_ECOSYSTEM_FILE=str(self.tmp / "eco.json"), PYTHONIOENCODING="utf-8")
        self.now = dt.datetime.now()
        # a transcript that makes the project known
        d = self.claude / "projects" / "p"
        d.mkdir(parents=True)
        (d / "s.jsonl").write_text(json.dumps({"type": "user", "cwd": str(self.proj)}) + "\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, jdir, entries, state=None):
        (jdir / "log").mkdir(parents=True, exist_ok=True)
        idx, log = [], []
        for when, tags, title, nxt in entries:
            log.append(f"## {when:%Y-%m-%d %H:%M} {' '.join('#' + t for t in tags)} — {title}\nDone: x\nNext: {nxt}\n")
            idx.append(f"{when:%Y-%m-%d} | x | {title}")
        (jdir / "log" / "2026-11.md").write_text("\n".join(log), encoding="utf-8")
        (jdir / "INDEX.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
        if state:
            (jdir / "STATE.md").write_text(state, encoding="utf-8")

    def run_b(self, *args):
        r = subprocess.run([sys.executable, str(SCRIPT), *args], env=self.env, capture_output=True,
                           text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_projects_topics_stale_and_superseded(self):
        d = lambda days: self.now - dt.timedelta(days=days)
        self.write(self.proj / ".journal", [(d(10), ["parser"], "Parser done", "add tests")],
                   state="# bot\nGoal: g\nIn progress: tokenizer\nNext steps: release 1.0\n")
        self.write(self.glob, [
            (d(3), ["setup", "plugins"], "Old setup", "pick a name"),
            (d(1), ["naming", "setup", "plugins"], "Name chosen", "rename repos"),
            (d(0), ["article"], "Article planned", "write draft"),
            (d(90), ["ancient"], "Very old", "nothing"),
        ])
        out = self.run_b("show")
        self.assertIn("■ bot — 10d ago · STALE: Parser done", out)
        self.assertIn("In progress: tokenizer", out)        # STATE beats the entry's Next
        self.assertNotIn("add tests", out)
        self.assertIn("#article — today", out)
        self.assertIn("#naming", out)
        self.assertNotIn("Old setup", out)                  # covered by a newer entry
        self.assertNotIn("Very old", out)                   # outside --days
        self.assertLess(out.index("#article"), out.index("bot —"))
        self.assertIn("Very old", self.run_b("show", "--days", "100"))

    def test_empty_and_where(self):
        self.assertIn("no journal activity", self.run_b("show"))
        self.write(self.glob, [(self.now, ["a"], "A", "b")])
        self.assertIn(str(self.glob), self.run_b("where"))

    def test_limits_block_runs_quoted_cmd(self):
        # ecosystem.json stores cmds as '"<python>" "<script>"' — on Windows the quotes must not reach exec
        fake = self.tmp / "dir with space" / "limits.py"
        fake.parent.mkdir()
        fake.write_text("import sys\nprint('[limits] OVER: x used $9 of $5')\n", encoding="utf-8")
        (self.tmp / "eco.json").write_text(json.dumps({"version": 1, "plugins": {
            "animus-limits": {"cmd": f'"{sys.executable}" "{fake}"'}}}), encoding="utf-8")
        self.write(self.glob, [(self.now, ["a"], "A", "b")])
        self.assertIn("[limits] OVER: x", self.run_b("show"))

    def test_line_cap(self):
        self.write(self.glob, [(self.now - dt.timedelta(minutes=i), [f"t{i}"], f"T{i}", "n") for i in range(30)])
        out = self.run_b("show", "--max-lines", "10")
        self.assertEqual(len(out.strip().splitlines()), 10)
        self.assertIn("more", out.strip().splitlines()[-1].lower() + " more")


if __name__ == "__main__":
    unittest.main()
