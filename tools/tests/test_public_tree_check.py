import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "public_tree_check.py"
spec = importlib.util.spec_from_file_location("scanner", SCRIPT)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)
TERM = "Private Fixture Recipient"


class PublicTreeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "--quiet")
        self.denied = scanner.policy(json.dumps([scanner.fingerprint(TERM)]))

    def git(self, *args):
        return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null", "-C", str(self.root), *args], stderr=subprocess.DEVNULL)

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "fixture")

    def check(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            found = scanner.scan(self.root, self.denied)
        self.assertNotIn(TERM, output.getvalue())
        return found

    def test_full_tree_not_only_diff_and_no_history(self):
        (self.root / "old.txt").write_text(TERM)
        self.commit()
        (self.root / "new.txt").write_text("safe")
        self.commit()
        self.assertEqual(self.check(), 1)
        (self.root / "old.txt").write_text("synthetic")
        self.commit()
        self.assertEqual(self.check(), 0)

    def test_normalization_and_utf16(self):
        (self.root / "case.txt").write_text("PRIVATE\nfixture-recipient")
        (self.root / "wide.txt").write_bytes(TERM.encode("utf-16"))
        (self.root / "unicode.txt").write_text("Ｐｒｉｖａｔｅ fixture recipient")
        self.commit()
        self.assertEqual(self.check(), 3)

    def test_paths_symlinks_and_no_external_read(self):
        (self.root / TERM).write_text("safe")
        (self.root / "link").symlink_to("/" + TERM)
        (self.root / "outside").symlink_to("/etc/passwd")
        self.commit()
        self.assertEqual(self.check(), 2)

    def test_scan_committed_not_worktree_or_untracked_content(self):
        (self.root / "file.txt").write_text(TERM)
        self.commit()
        (self.root / "file.txt").write_text("safe worktree")
        (self.root / "untracked").write_text(TERM)
        self.assertEqual(self.check(), 1)

    def test_policy_failure_is_closed_without_echoing_input(self):
        for value in ["", "[]", "{}", "[null]", '[{"words":true,"sha256":"x"}]']:
            result = subprocess.run(["python3", str(SCRIPT), str(self.root)],
                                    env={**os.environ, "PUBLIC_TREE_DENYLIST": value}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_cli_rejects_synthetic_term_and_allows_clean_tree(self):
        (self.root / "fixture.txt").write_text(TERM)
        self.commit()
        env = {**os.environ, "PUBLIC_TREE_DENYLIST": json.dumps([scanner.fingerprint(TERM)])}
        result = subprocess.run(["python3", str(SCRIPT), str(self.root)], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(TERM, result.stdout + result.stderr)
        (self.root / "fixture.txt").write_text("safe")
        self.commit()
        self.assertEqual(subprocess.run(["python3", str(SCRIPT), str(self.root)], env=env, capture_output=True).returncode, 0)
