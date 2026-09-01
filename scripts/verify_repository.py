#!/usr/bin/env python3
"""Validate the repository's source records without network access."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess


TEXT_SUFFIXES = {
    ".cjs",
    ".csv",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsv",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
CONFLICT_MARKER = re.compile(r"(?m)^(?:<{7} .+|={7}|>{7} .+)$")


def tracked_files(root: pathlib.Path) -> list[pathlib.Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [root / item.decode() for item in result.stdout.split(b"\0") if item]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--output-root", type=pathlib.Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    files = tracked_files(root)
    if not files:
        raise SystemExit("repository has no tracked files")

    tree = hashlib.sha256()
    text_count = 0
    json_count = 0
    for path in files:
        relative = path.relative_to(root).as_posix()
        payload = path.read_bytes()
        if not payload:
            raise SystemExit(f"tracked file is empty: {relative}")
        tree.update(relative.encode())
        tree.update(b"\0")
        tree.update(hashlib.sha256(payload).digest())

        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text_count += 1
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise SystemExit(f"text file is not UTF-8: {relative}: {error}") from error
        if CONFLICT_MARKER.search(text):
            raise SystemExit(f"merge-conflict marker remains in {relative}")
        if any(line.rstrip("\n\r") != line.rstrip("\n\r ") for line in text.splitlines(True)):
            raise SystemExit(f"trailing whitespace remains in {relative}")
        if path.suffix.lower() == ".md" and not text.lstrip().startswith("#"):
            raise SystemExit(f"Markdown file has no leading heading: {relative}")
        if path.suffix.lower() == ".json":
            json.loads(text)
            json_count += 1

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    receipt = {
        "schema_version": 1,
        "commit": commit,
        "tracked_file_count": len(files),
        "text_file_count": text_count,
        "json_file_count": json_count,
        "tree_sha256": tree.hexdigest(),
    }
    (output_root / "repository-validation.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
