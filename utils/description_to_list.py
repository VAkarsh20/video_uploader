"""Convert a simple markdown file into a list of text segments.

Expected MD format:
1. Title (single line)
2. Synopsis (single paragraph)
3..n. Thoughts (one or more paragraphs), terminated by a line containing a single dash `-`
Last. Hashtags (single line starting with `#`)

Usage: import from `utils.description_to_list` and call `description_to_list(Path)`
"""

import json
import sys
from pathlib import Path


def description_to_list(path: Path):
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    lines = text.splitlines()

    # Title is the first non-empty line
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx >= len(lines):
        return []
    title = lines[idx].strip()
    idx += 1

    # Synopsis: next non-empty paragraph (lines until an empty line)
    # Gather until we hit a blank line
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    synopsis_lines = []
    while idx < len(lines) and lines[idx].strip():
        synopsis_lines.append(lines[idx])
        idx += 1
    synopsis = "\n".join([l.rstrip() for l in synopsis_lines]).strip()

    # Thoughts: collect lines until a line that is exactly '-'
    thoughts_lines = []
    # skip blank lines between synopsis and thoughts
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    while idx < len(lines):
        if lines[idx].strip() == "-":
            idx += 1
            break
        thoughts_lines.append(lines[idx])
        idx += 1
    thoughts = "\n".join([l.rstrip() for l in thoughts_lines]).strip()

    # Skip blanks, then hashtags line(s). We'll take the next non-empty line(s) that start with '#'
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    hashtags = ""
    if idx < len(lines):
        # join remaining lines that start with '#'
        tag_lines = []
        while idx < len(lines) and lines[idx].strip().startswith("#"):
            tag_lines.append(lines[idx].strip())
            idx += 1
        hashtags = " ".join(tag_lines).strip()

    parts = [title]
    if synopsis:
        parts.append(synopsis)
    if thoughts:
        parts.append(thoughts)
    if hashtags:
        parts.append(hashtags)

    return parts


def main():
    if len(sys.argv) < 2:
        print("Usage: md_to_list.py path/to/file.md", file=sys.stderr)
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(2)
    parts = description_to_list(path)
    print(json.dumps(parts, ensure_ascii=False))


if __name__ == "__main__":
    main()
