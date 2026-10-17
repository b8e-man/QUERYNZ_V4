"""One small file per card, lesson and queued decision; this reads them.

A record is: a first line (the title; for a lesson, the rule itself), then
`key: value` lines until the first blank line, then the body. The generators
in bin/ read every record in a folder and write the one file nobody edits:
the card board, the parking list, the lessons index, the decision queue."""
import os
import re

FIELD = re.compile(r"^([a-z][a-z-]*):\s*(.*)$")


def read_record(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    title = lines[0].lstrip("# ").strip() if lines else ""
    fields, i = {}, 1
    while i < len(lines) and lines[i].strip():
        m = FIELD.match(lines[i])
        if not m:
            raise ValueError(f"{path}:{i + 1}: expected `key: value`, got {lines[i]!r}")
        fields[m.group(1)] = m.group(2).strip()
        i += 1
    body = "\n".join(lines[i + 1:]).strip()
    return {"path": path, "name": os.path.splitext(os.path.basename(path))[0], "title": title,
            "fields": fields, "body": body}


def read_folder(folder: str, skip=("INDEX.md", "README.md")) -> list:
    out = []
    for f in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        if f.endswith(".md") and f not in skip:
            out.append(read_record(os.path.join(folder, f)))
    return out


def write_if_changed(path: str, text: str) -> bool:
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old == text:
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return True
