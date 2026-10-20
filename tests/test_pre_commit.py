"""Verify the staged-file budget through isolated Git repositories."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HOOK = Path(__file__).resolve().parents[1] / ".githooks/pre-commit"
LIMIT = 20_000


class PreCommitTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        self.git("init", "--quiet")
        self.git("config", "user.name", "Hook test")
        self.git("config", "user.email", "hook-test@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", ".git/hooks")
        self.hook = self.root / ".git/hooks/pre-commit"
        shutil.copy2(HOOK, self.hook)

    def git(self, *args, check=True):
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            env=self.env, check=check, capture_output=True, text=True,
        )

    def write(self, path, content):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)

    def stage(self, *paths):
        self.git("--literal-pathspecs", "add", "--", *paths)

    def baseline(self):
        self.git("commit", "--quiet", "--no-verify", "-m", "Fixture baseline")

    def run_hook(self):
        return subprocess.run(
            [sys.executable, str(self.hook)], cwd=self.root, env=self.env,
            capture_output=True, text=True,
        )

    def assert_passes(self):
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def assert_rejected(self, *paths, result=None):
        result = result or self.run_hook()
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        self.assertNotIn("Traceback", output)
        for path in paths:
            representations = (
                path,
                repr(path)[1:-1],
                json.dumps(path, ensure_ascii=True)[1:-1],
                json.dumps(path, ensure_ascii=False)[1:-1],
            )
            self.assertTrue(any(name in output for name in representations), output)
        return output

    def test_first_commit_accepts_exact_limit_and_rejects_one_more_byte(self):
        self.write("empty.txt", b"")
        self.write("script.py", b"x" * LIMIT)
        (self.root / "script.py").chmod(0o755)
        self.stage("empty.txt", "script.py")
        self.assert_passes()
        self.write("script.py", b"x" * (LIMIT + 1))
        self.stage("script.py")
        output = self.assert_rejected("script.py").replace(",", "")
        self.assertIn("20001", output)
        self.assertIn("5000.25", output)
        self.assertRegex(output.lower(), r"token|トークン")

    def test_multibyte_text_uses_blob_bytes(self):
        content = ("日本語" * 2222).encode("utf-8") + b"ab"
        self.assertEqual(len(content), LIMIT)
        self.write("日本語.md", content)
        self.stage("日本語.md")
        self.assert_passes()
        self.write("日本語.md", content + b"x")
        self.stage("日本語.md")
        self.assert_rejected("日本語.md")

    def test_binary_regular_file_has_the_same_budget(self):
        self.write("data.bin", b"\0" * (LIMIT + 1))
        self.stage("data.bin")
        self.assert_rejected("data.bin")

    def test_full_blob_is_checked_after_a_one_byte_diff(self):
        self.write("existing.txt", b"x" * LIMIT)
        self.stage("existing.txt")
        self.baseline()
        self.write("existing.txt", b"x" * (LIMIT + 1))
        self.stage("existing.txt")
        self.assert_rejected("existing.txt")

    def test_small_index_version_passes_when_worktree_version_is_large(self):
        self.write("partial.md", b"x" * LIMIT)
        self.stage("partial.md")
        self.write("partial.md", b"x" * (LIMIT + 1))
        self.assert_passes()

    def test_large_index_version_fails_when_worktree_version_is_small(self):
        self.write("partial.md", b"x" * (LIMIT + 1))
        self.stage("partial.md")
        self.write("partial.md", "small worktree version\n")
        self.assert_rejected("partial.md")

    def test_untracked_unstaged_and_unchanged_tracked_files_are_ignored(self):
        self.write("unchanged.md", b"x" * (LIMIT + 1))
        self.write("unstaged.md", "baseline\n")
        self.stage("unchanged.md", "unstaged.md")
        self.baseline()
        self.write("unstaged.md", b"x" * (LIMIT + 1))
        self.write("untracked.md", b"x" * (LIMIT + 1))
        self.write("changed.md", "small staged file\n")
        self.stage("changed.md")
        self.assert_passes()

    def test_rename_checks_destination_blob_and_deletion_is_ignored(self):
        self.write("old.md", b"x" * (LIMIT + 1))
        self.stage("old.md")
        self.baseline()
        self.git("mv", "--", "old.md", "renamed.md")
        self.assert_rejected("renamed.md")
        self.git("rm", "--force", "--", "renamed.md")
        self.assert_passes()

    def test_symlink_and_gitlink_are_not_regular_files(self):
        self.git("commit", "--quiet", "--allow-empty", "--no-verify", "-m", "x" * (LIMIT + 1))
        commit = self.git("rev-parse", "HEAD").stdout.strip()
        self.write("large-target.txt", b"x" * (LIMIT + 1))
        (self.root / "target-link").symlink_to("large-target.txt")
        self.stage("target-link")
        self.git("update-index", "--add", "--cacheinfo", f"160000,{commit},submodule")
        self.assert_passes()

    def test_nul_safe_literal_paths_are_all_checked(self):
        paths = ("space and\nnewline.md", "-leading.md", ":(glob)*.md", "[wild]?*.md")
        for path in paths:
            self.write(path, b"x" * (LIMIT + 1))
        self.stage(*paths)
        self.assert_rejected(*paths)

    def test_common_lockfile_names_are_excluded_in_any_directory(self):
        paths = (
            "deps/package-lock.json", "Cargo.lock", "frontend/pnpm-lock.yaml",
            "yarn.lock", "poetry.lock", "Gemfile.lock",
        )
        for path in paths:
            self.write(path, b"x" * (LIMIT + 1))
        self.stage(*paths)
        self.assert_passes()

    def test_staged_generated_vendored_and_nonagent_attributes_exclude_files(self):
        attributes = {
            "generated-set.py": "linguist-generated",
            "generated-true.py": "linguist-generated=true",
            "vendored-set.py": "linguist-vendored",
            "vendored-true.py": "linguist-vendored=true",
            "nonagent-unset.py": "-agent-authored",
            "nonagent-false.py": "agent-authored=false",
        }
        self.write(".gitattributes", "".join(f"{path} {attrs}\n" for path, attrs in attributes.items()))
        for path in attributes:
            self.write(path, b"x" * (LIMIT + 1))
        self.stage(".gitattributes", *attributes)
        self.assert_passes()

    def test_false_or_unknown_exclusion_attributes_do_not_bypass_check(self):
        attributes = {
            "generated-false.py": "linguist-generated=false",
            "generated-unset.py": "-linguist-generated",
            "generated-unknown.py": "linguist-generated=unknown",
            "vendored-false.py": "linguist-vendored=false",
            "vendored-unknown.py": "linguist-vendored=unknown",
            "authorship-unknown.py": "agent-authored=unknown",
        }
        self.write(".gitattributes", "".join(f"{path} {attrs}\n" for path, attrs in attributes.items()))
        for path in attributes:
            self.write(path, b"x" * (LIMIT + 1))
        self.stage(".gitattributes", *attributes)
        self.assert_rejected(*attributes)

    def test_explicit_agent_authorship_overrides_lock_and_generated_exclusions(self):
        attributes = {
            "package-lock.json": "agent-authored",
            "Cargo.lock": "agent-authored=true",
            "generated.py": "linguist-generated=true agent-authored",
            "vendor/library.py": "linguist-vendored agent-authored=true",
        }
        self.write(".gitattributes", "".join(f"{path} {attrs}\n" for path, attrs in attributes.items()))
        for path in attributes:
            self.write(path, b"x" * (LIMIT + 1))
        self.stage(".gitattributes", *attributes)
        self.assert_rejected(*attributes)

    def test_attributes_use_index_in_both_directions(self):
        self.write(".gitattributes", "")
        self.stage(".gitattributes")
        self.baseline()
        self.write("generated.py", b"x" * (LIMIT + 1))
        self.stage("generated.py")
        self.write(".gitattributes", "generated.py linguist-generated\n")
        self.assert_rejected("generated.py")
        self.stage(".gitattributes")
        self.assert_passes()
        self.write(".gitattributes", "")
        self.assert_passes()
        self.stage(".gitattributes")
        self.assert_rejected("generated.py")

    def test_each_violation_has_size_and_actionable_split_guidance(self):
        self.write("module.py", b"x" * (LIMIT + 1))
        self.write("guide.md", b"x" * 24_000)
        self.stage("module.py", "guide.md")
        output = self.assert_rejected("module.py", "guide.md").replace(",", "")
        for value in ("20001", "5000.25", "24000", "6000"):
            self.assertIn(value, output)
        for concept in (
            r"responsibilit|責務", r"test|テスト", r"Markdown",
            r"heading|見出し", r"link|リンク", r"git add", r"commit",
        ):
            self.assertRegex(output, f"(?i){concept}")

    def test_real_commit_is_blocked_then_succeeds_after_restaging_fix(self):
        self.write("document.md", b"x" * (LIMIT + 1))
        self.stage("document.md")
        rejected = self.git("commit", "--quiet", "-m", "Must be rejected", check=False)
        self.assert_rejected("document.md", result=rejected)
        self.assertNotEqual(self.git("rev-parse", "--verify", "HEAD", check=False).returncode, 0)
        self.write("document.md", "small staged document\n")
        self.stage("document.md")
        self.git("commit", "--quiet", "-m", "Accepted after fixing")
        self.assertEqual(self.git("show", "HEAD:document.md").stdout, "small staged document\n")


if __name__ == "__main__":
    unittest.main()
