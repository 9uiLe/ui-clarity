"""Exercise the public checker CLI against isolated Git repositories."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[1] / "scripts/check_repository.py"
SKILL = "skills/ui-clarity"
VALID_SKILL = "---\nname: ui-clarity\ndescription: A small example skill.\n---\n\n[Reference](references/guide.md)\n"


class RepositoryChecksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "--quiet")
        self.write(f"{SKILL}/SKILL.md", VALID_SKILL)
        self.write(f"{SKILL}/references/guide.md", "# Reference\n")
        for entry in (".agents/skills/ui-clarity", ".claude/skills/ui-clarity"):
            self.link(entry, "../../skills/ui-clarity")
        self.git("add", "--all")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def write(self, path, content):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")

    def link(self, path, target):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        if file.is_symlink() or file.exists():
            file.unlink()
        file.symlink_to(target)

    def run_check(self, *args):
        return subprocess.run(
            [sys.executable, str(CHECKER), "--root", str(self.root), *args],
            capture_output=True, text=True,
        )

    def assert_passes(self, *args):
        result = self.run_check(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Repository checks passed", result.stdout)

    def assert_fails(self, message, *args):
        result = self.run_check(*args)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(message, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def test_valid_repository(self):
        self.assert_passes()

    def test_frontmatter_must_be_safe_and_well_formed(self):
        for metadata in (
            "name: other\ndescription: Example",
            "name: ui-clarity\ndescription: 123",
            "name: ui-clarity\ndescription: ''",
            "name: [broken",
            "!!python/object/apply:os.system ['SECRET CONTENT']",
        ):
            with self.subTest(metadata=metadata):
                self.write(f"{SKILL}/SKILL.md", f"---\n{metadata}\n---\n")
                result = self.assert_fails("invalid YAML frontmatter")
                self.assertNotIn("SECRET CONTENT", result.stderr)

    def test_missing_frontmatter(self):
        self.write(f"{SKILL}/SKILL.md", "# No metadata\n")
        self.assert_fails("invalid YAML frontmatter")

    def test_missing_link(self):
        self.write(f"{SKILL}/SKILL.md", VALID_SKILL + "[Missing](references/missing.md)\n")
        self.assert_fails("local Markdown link is missing")

    def test_local_untracked_reference_is_not_publishable_by_default(self):
        self.write(f"{SKILL}/references/local.md", "# Local\n")
        self.write(f"{SKILL}/SKILL.md", VALID_SKILL + "[Local](references/local.md)\n")
        self.assert_fails("local Markdown link is missing")
        self.assert_passes("--include-untracked")

    def test_escaping_and_absolute_links(self):
        for target in ("../../outside.md", "%2e%2e/%2e%2e/outside.md", "/tmp/outside.md", "file:///tmp/outside.md", "C:\\outside.md"):
            with self.subTest(target=target):
                self.write(f"{SKILL}/SKILL.md", VALID_SKILL + f"[Escape]({target})\n")
                self.assert_fails("local Markdown link")

    def test_inline_image_and_reference_definition_links(self):
        self.write(f"{SKILL}/SKILL.md", VALID_SKILL + "![Image](missing.svg)\n[guide]: <missing.md>\n")
        result = self.assert_fails("local Markdown link is missing")
        self.assertEqual(result.stderr.count("local Markdown link is missing"), 2)

    def test_external_anchors_titles_and_code_are_not_missing_files(self):
        self.write(f"{SKILL}/SKILL.md", VALID_SKILL + """
[External](https://example.com/missing.md)
[Mail](mailto:example@example.com)
[Heading](#heading)
[With title](references/guide.md "Guide")
[Reference]: <references/guide.md> "Guide"
`[Example](missing.md)`
```md
[Example](missing.md)
```
""")
        self.assert_passes()

    def test_duplicate_skill_entry(self):
        self.write("skills/second/SKILL.md", "---\nname: second\ndescription: Duplicate\n---\n")
        self.git("add", "--all")
        self.assert_fails("Expected exactly one skill entry")

    def test_duplicate_public_entry(self):
        self.link(".agents/skills/duplicate", "../../skills/ui-clarity")
        self.git("add", "--all")
        self.assert_fails("unexpected public skill entry")

    def test_required_entries_must_be_selected_by_git(self):
        for path in (f"{SKILL}/SKILL.md", ".agents/skills/ui-clarity", ".claude/skills/ui-clarity"):
            with self.subTest(path=path):
                self.git("rm", "--cached", "--", path)
                self.assert_fails("required public file is absent")
                self.assert_passes("--include-untracked")
                self.git("add", "--", path)

    def test_broken_and_absolute_entry_symlinks(self):
        for target, expected in (("../../missing", "cannot be resolved"), (str(self.root / SKILL), "must be relative")):
            with self.subTest(target=target):
                self.link(".agents/skills/ui-clarity", target)
                self.assert_fails(expected)

    def test_entry_must_target_the_distributed_skill(self):
        self.link(".agents/skills/ui-clarity", "../../tests")
        self.write("tests/example.md", "Example")
        self.assert_fails("public entry must be a symlink")

    def test_outside_symlink(self):
        with tempfile.TemporaryDirectory() as outside:
            relative = os.path.relpath(outside, self.root)
            self.link("outside-link", relative)
            self.git("add", "--all")
            self.assert_fails("symlink target escapes the repository")

    def test_distributed_symlink_must_stay_inside_skill(self):
        self.write("outside.md", "# Outside skill\n")
        self.link(f"{SKILL}/references/guide.md", "../../../outside.md")
        self.git("add", "--all")
        self.assert_fails("distributed skill file resolves outside the skill")

    def test_symlink_target_must_be_selected_by_git(self):
        self.write("local-only.md", "# Only exists locally\n")
        self.link("public-link.md", "local-only.md")
        self.git("add", "--", "public-link.md")
        self.assert_fails("symlink target is absent")
        self.assert_passes("--include-untracked")

    def test_symlink_cycle_is_a_failure_without_traceback(self):
        self.link(f"{SKILL}/references/guide.md", "guide.md")
        self.assert_fails("cannot be resolved")

    def test_symlink_to_private_record_is_rejected_before_content_scan(self):
        self.write(".moletta-runs/record", "-----BEGIN " + "PRIVATE KEY-----\nsecret\n")
        self.link("alias.md", ".moletta-runs/record")
        self.git("add", "--", "alias.md")
        result = self.assert_fails("resolves to a private path")
        self.assertNotIn("possible credential", result.stderr)

    def test_private_paths(self):
        for path in (".moletta-runs/private.json", ".env", ".env.local", ".aws/credentials", "key.key"):
            with self.subTest(path=path):
                self.write(path, "PRIVATE CONTENT MUST NOT BE PRINTED")
                self.git("add", "--", path)
                result = self.assert_fails("private path must not be published")
                self.assertNotIn("PRIVATE CONTENT", result.stderr)
                self.git("rm", "--cached", "--", path)
                (self.root / path).unlink()

    def test_env_example_is_allowed(self):
        self.write(".env.example", "EXAMPLE_VALUE=replace-me\n")
        self.git("add", "--all")
        self.assert_passes()

    def test_private_key_and_credential_signatures(self):
        for content in ("-----BEGIN " + "PRIVATE KEY-----\nsecret\n", "AKIA" + "X" * 16):
            with self.subTest(content_kind=content[:4]):
                self.write("notes.txt", content)
                self.git("add", "--all")
                result = self.assert_fails("possible credential or private key")
                self.assertNotIn(content.strip(), result.stderr)

    def test_untracked_local_files_are_excluded_unless_requested(self):
        self.link(".agents/skills/local-helper", "/not-a-public-skill")
        self.write(".env", "DO NOT READ")
        self.assert_passes()
        self.assert_fails("private path must not be published", "--include-untracked")

    def test_ignored_files_remain_excluded_with_include_untracked(self):
        self.write(".gitignore", "local-only/\n")
        self.git("add", "--all")
        self.write("local-only/.env", "DO NOT READ")
        self.assert_passes("--include-untracked")

    def test_nul_safe_git_file_names(self):
        self.write("tests/file with spaces\nand newline.html", "<html><button></button></html>")
        self.git("add", "--all")
        self.assert_passes()

    def test_intentionally_bad_html_is_not_linted(self):
        self.write("tests/fixtures/bad.html", "<div onclick='doThing()'><a>Broken UI</a></div>")
        self.git("add", "--all")
        self.assert_passes()


if __name__ == "__main__":
    unittest.main()
