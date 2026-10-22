"""A workbook's cells as text, sheet by sheet, row by row, with the standard
library only (the estate carries no spreadsheet package). Shared, inline and
plain cells are read; a formula gives its stored value; a cell styled as a
date gives its serial number, which the reading turns into a date only in a
column its profile names a date. Each row keeps its sheet name and its row
number, so a row's place in the workbook is its citation.

    sheets(data)    [(sheet name, [(row number, {column number: text})])]
"""
import datetime as dt
import io
import re
import xml.etree.ElementTree as ET
import zipfile

_M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_PR = "{http://schemas.openxmlformats.org/package/2006/relationships}"


class NotAWorkbook(ValueError):
    pass


def col_number(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n


def _text(el) -> str:
    return "".join(t.text or "" for t in el.iter(_M + "t"))


def sheets(data: bytes) -> list:
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        book = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        raise NotAWorkbook(f"not an xlsx workbook: {type(exc).__name__}")
    target = {r.get("Id"): r.get("Target") for r in rels.iter(_PR + "Relationship")}
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        shared = [_text(si) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(_M + "si")]
    out = []
    for s in book.iter(_M + "sheet"):
        path = target.get(s.get(_R + "id"), "")
        path = path.lstrip("/") if path.startswith("/") else "xl/" + path
        rows = []
        for row in ET.fromstring(z.read(path)).iter(_M + "row"):
            cells = {}
            for c in row.iter(_M + "c"):
                t, v = c.get("t"), c.find(_M + "v")
                if t == "s" and v is not None:
                    val = shared[int(v.text)]
                elif t == "inlineStr":
                    val = _text(c)
                else:
                    val = v.text if v is not None and v.text is not None else ""
                val = " ".join(val.split())
                if val:
                    cells[col_number(c.get("r"))] = val
            if cells:
                rows.append((int(row.get("r")), cells))
        out.append((s.get("name"), rows))
    return out


def serial_date(text: str):
    """An Excel serial day number (1900 system) as a date; None for anything else."""
    try:
        n = float(text)
    except (TypeError, ValueError):
        return None
    if not 20000 < n < 80000:
        return None
    return dt.date(1899, 12, 30) + dt.timedelta(days=int(n))
