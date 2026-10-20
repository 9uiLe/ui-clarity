#!/usr/bin/env python3
"""Check the publishable file set; behavior of the skill is tested manually."""

import argparse
import ntpath
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import yaml


SKILL = PurePosixPath("skills/ui-clarity")
ENTRY_POINTS = (
    PurePosixPath(".agents/skills/ui-clarity"),
    PurePosixPath(".claude/skills/ui-clarity"),
)
PRIVATE_KEY = re.compile(rb"(?m)^-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----")
CREDENTIAL = re.compile(
    rb"\b(?:AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|"
    rb"github_pat_[A-Za-z0-9_]{20,})\b"
)
# Deliberately a small Markdown subset: inline links/images and reference definitions.
LINK = re.compile(
    r"!?\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s)]+))"
    r"(?:[ \t]+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^\n)]*\)))?[ \t]*\)"
)
REFERENCE = re.compile(r"^ {0,3}\[[^\]\n]+\]:[ \t]*(?:<([^>\n]+)>|(\S+))", re.M)


def inside(path, directory):
    return path == directory or directory in path.parents


def destinations(markdown):
    """Ignore code examples, then yield supported Markdown link destinations."""
    lines = []
    fence = None
    for line in markdown.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            continue
        if marker:
            fence = marker[1]
            continue
        lines.append(line)
    prose = re.sub(r"(`+).*?\1", "", "\n".join(lines))
    for pattern in (LINK, REFERENCE):
        for match in pattern.finditer(prose):
            yield match[1] or match[2]


def private_path(path):
    name = path.name.lower()
    return (
        ".moletta-runs" in (part.lower() for part in path.parts)
        or (name == ".env" or name.startswith(".env.")) and name != ".env.example"
        or name in {"credentials", "credentials.json", "application_default_credentials.json",
                    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
        or path.suffix.lower() in {".key", ".p12", ".pfx"}
    )


def check(root, include_untracked=False):
    errors = []

    def fail(path, message):
        errors.append(f"{str(path)!r}: {message}")

    command = ["git", "-C", str(root), "ls-files", "-z", "--cached"]
    if include_untracked:
        command += ["--others", "--exclude-standard"]
    try:
        result = subprocess.run(command, check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        return ["Could not list repository files with git."], 0
    paths = {PurePosixPath(os.fsdecode(value)) for value in result.stdout.split(b"\0") if value}
    required = {SKILL / "SKILL.md", *ENTRY_POINTS}
    for path in sorted(required - paths):
        fail(path, "required public file is absent from the selected Git file set")
    skill_entries = {p for p in paths if p.parts[0] == "skills" and p.name == "SKILL.md"}
    if skill_entries != {SKILL / "SKILL.md"}:
        errors.append("Expected exactly one skill entry: 'skills/ui-clarity/SKILL.md'.")

    safe_files = {}
    skill_root = root / SKILL
    for path in sorted(paths):
        if path.is_absolute() or ".." in path.parts:
            fail(path, "path escapes the repository")
            continue
        if private_path(path):
            fail(path, "private path must not be published")
            continue  # Never read private records or their contents.
        local = root / path
        is_link = local.is_symlink()
        if is_link:
            target = os.readlink(local)
            if os.path.isabs(target) or ntpath.isabs(target):
                fail(path, "symlink target must be relative")
                continue
        try:
            resolved = local.resolve(strict=True)
        except (OSError, RuntimeError):
            fail(path, "file or symlink target is missing or cannot be resolved")
            continue
        if not inside(resolved, root):
            fail(path, "file or symlink target escapes the repository")
            continue
        relative_target = PurePosixPath(resolved.relative_to(root).as_posix())
        if private_path(relative_target):
            fail(path, "file or symlink resolves to a private path")
            continue
        if is_link:
            if relative_target not in paths and not any(inside(p, relative_target) for p in paths):
                fail(path, "symlink target is absent from the selected Git file set")
        if path in ENTRY_POINTS:
            if not is_link or resolved != skill_root:
                fail(path, "public entry must be a symlink to skills/ui-clarity")
        elif any(path.parts[:2] == entry.parts[:2] for entry in ENTRY_POINTS):
            fail(path, "unexpected public skill entry")
        if inside(path, SKILL) and not inside(resolved, skill_root):
            fail(path, "distributed skill file resolves outside the skill")
            continue
        if local.is_file():
            try:
                content = local.read_bytes()
            except OSError:
                fail(path, "file could not be read")
                continue
            if PRIVATE_KEY.search(content) or CREDENTIAL.search(content):
                fail(path, "possible credential or private key must not be published")
            safe_files[path] = content
        elif not is_link:
            fail(path, "selected path is not a regular file or symlink")

    skill_file = SKILL / "SKILL.md"
    if skill_file in safe_files:
        try:
            text = safe_files[skill_file].decode("utf-8")
            lines = text.splitlines()
            end = lines.index("---", 1) if lines and lines[0] == "---" else 0
            metadata = yaml.safe_load("\n".join(lines[1:end])) if end else None
            if not isinstance(metadata, dict):
                raise ValueError
            name, description = metadata.get("name"), metadata.get("description")
            if name != SKILL.name or not isinstance(description, str) or not description.strip():
                raise ValueError
        except (UnicodeError, ValueError, yaml.YAMLError):
            fail(skill_file, "invalid YAML frontmatter: expected matching name and nonempty description")

    for path, content in safe_files.items():
        if not inside(path, SKILL) or path.suffix.lower() != ".md":
            continue
        try:
            text = content.decode("utf-8")
        except UnicodeError:
            fail(path, "Markdown must be valid UTF-8")
            continue
        for destination in destinations(text):
            destination = re.sub(r"\\([\\`*{}\[\]()#+\-.!<>_ ])", r"\1", destination)
            if ntpath.isabs(destination) and not destination.startswith("/"):
                fail(path, "local Markdown link must be relative to the skill")
                continue
            try:
                url = urlsplit(destination)
            except ValueError:
                fail(path, "invalid Markdown link destination")
                continue
            if url.scheme.lower() == "file":
                fail(path, "local Markdown link must be relative to the skill")
                continue
            if url.scheme or url.netloc or not url.path:
                continue
            target = unquote(url.path)
            if os.path.isabs(target) or ntpath.isabs(target):
                fail(path, "local Markdown link must be relative to the skill")
                continue
            try:
                candidate = (root / path.parent / target).resolve()
            except (OSError, RuntimeError, ValueError):
                fail(path, "local Markdown link cannot be resolved")
                continue
            if not inside(candidate, skill_root):
                fail(path, "local Markdown link escapes the skill")
                continue
            relative = PurePosixPath(candidate.relative_to(root).as_posix())
            if relative not in paths or not candidate.is_file():
                fail(path, "local Markdown link is missing from the selected Git file set")
    return errors, len(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--include-untracked", action="store_true", help="also inspect nonignored untracked files")
    args = parser.parse_args()
    errors, count = check(args.root.resolve(), args.include_untracked)
    if errors:
        print("Repository checks failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Repository checks passed ({count} selected files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
