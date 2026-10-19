"""A workbook's cells, read with the standard library alone (the estate's
environment has no spreadsheet package, and a reader that depends on one
would be a second thing to keep). Two formats are held:

  .xlsx   a zip of XML parts (Office Open XML): read here directly
  .xls    the older binary format (BIFF8 inside an OLE2 compound file),
          the ministers' releases of 2008 to 2014: `biff.py`

Every cell keeps its reference ("C7"), the value as the file stores it
(a number for a number, the text for text) and, for a formula, the
formula and its cached result. A formula with no cached result is a
formula with no value, never zero.

    Cell(ref, row, col, value, text, formula)
    sheets(data, name)    [(sheet name, [Cell…])] in workbook order
    grid(cells)           {row: {col: Cell}}
"""
import io
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "pr": "http://schemas.openxmlformats.org/package/2006/relationships"}
_REF = re.compile(r"^([A-Z]+)(\d+)$")


@dataclass(frozen=True)
class Cell:
    ref: str            # "C7"
    row: int            # from 1
    col: int            # from 1
    value: object       # float, str, bool or None (a formula with no cached result)
    text: str           # the value as the file stores it, for `printed`
    formula: str = ""


def col_number(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n


def col_letters(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def ref_of(row: int, col: int) -> str:
    return f"{col_letters(col)}{row}"


def _text(el) -> str:
    """A shared or inline string: every <t> under it, rich-text runs joined."""
    return "".join(t.text or "" for t in el.iter(f"{{{NS['m']}}}t"))


def _xlsx(data: bytes) -> list:
    z = zipfile.ZipFile(io.BytesIO(data))
    names = set(z.namelist())
    shared = []
    if "xl/sharedStrings.xml" in names:
        shared = [_text(si) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)]
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")).findall("pr:Relationship", NS)}
    out = []
    for s in ET.fromstring(z.read("xl/workbook.xml")).find("m:sheets", NS).findall("m:sheet", NS):
        target = rels[s.get(f"{{{NS['r']}}}id")].lstrip("/")
        part = target if target.startswith("xl/") else "xl/" + target
        cells = []
        for c in ET.fromstring(z.read(part)).iter(f"{{{NS['m']}}}c"):
            m = _REF.match(c.get("r") or "")
            if not m:
                continue
            t, v, f = c.get("t"), c.find("m:v", NS), c.find("m:f", NS)
            raw = v.text if v is not None and v.text is not None else None
            if t == "s" and raw is not None:
                value = text = shared[int(raw)]
            elif t == "inlineStr":
                is_ = c.find("m:is", NS)
                value = text = _text(is_) if is_ is not None else ""
            elif t in ("str", "e"):
                value = text = raw
            elif t == "b":
                value, text = (raw == "1") if raw is not None else None, raw or ""
            else:
                value, text = (float(raw) if raw not in (None, "") else None), raw or ""
            formula = (f.text or "") if f is not None else ""
            if value is None and not formula and text == "":
                continue
            cells.append(Cell(c.get("r"), int(m.group(2)), col_number(m.group(1)), value, text or "", formula))
        out.append((s.get("name"), cells))
    return out


def sheets(data: bytes, name: str = "") -> list:
    if data[:4] == b"PK\x03\x04":
        return _xlsx(data)
    if data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        from registers.expenses import biff
        return biff.sheets(data)
    raise ValueError(f"{name or 'the document'} is neither an xlsx zip nor an OLE2 workbook")


def grid(cells: list) -> dict:
    out = {}
    for c in cells:
        out.setdefault(c.row, {})[c.col] = c
    return out
