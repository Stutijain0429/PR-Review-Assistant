"""
Splits a full multi-file unified diff (like what GitHub returns) into
per-file chunks, so we can review each changed file separately.
"""

import re
from typing import List, NamedTuple


class FileDiff(NamedTuple):
    filename: str
    diff_text: str


def split_diff_by_file(full_diff: str) -> List[FileDiff]:
    """
    A unified diff looks like:
        diff --git a/foo.py b/foo.py
        index abc123..def456 100644
        --- a/foo.py
        +++ b/foo.py
        @@ ... @@
        ...
        diff --git a/bar.py b/bar.py
        ...
    This splits it into one FileDiff per 'diff --git' section.
    """
    # Split on lines starting with "diff --git", keeping the delimiter
    chunks = re.split(r"(?=^diff --git )", full_diff, flags=re.MULTILINE)

    file_diffs = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # Extract filename from "diff --git a/path b/path"
        match = re.match(r"diff --git a/(.+?) b/(.+)", chunk)
        if not match:
            continue

        filename = match.group(2)  # use the "b/" (new) path
        file_diffs.append(FileDiff(filename=filename, diff_text=chunk))

    return file_diffs


def is_python_file(filename: str) -> bool:
    return filename.endswith(".py")

def extract_new_code(diff_text: str) -> str:
    """
    Rebuilds the 'after' version of the changed code from a unified diff:
    keeps added lines ('+') and unchanged context lines (' '),
    drops removed lines ('-') and diff headers.
    """
    lines = []
    in_header = False

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            in_header = True
            continue
        if line.startswith("@@"):
            in_header = False
            continue
        if in_header:
            continue

        if line.startswith("+") or line.startswith(" "):
            lines.append(line[1:])
        # '-' lines and "\ No newline at end of file" are dropped

    return "\n".join(lines)