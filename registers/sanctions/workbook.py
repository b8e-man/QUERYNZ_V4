"""A workbook's rows, read with the standard library alone (the estate's
environment has no spreadsheet package; a lane never imports another lane's
reader, so this is the sanctions lane's own, after `registers/expenses/sheet.py`).

    sheets(data)    [(sheet name, {row number: {column number: text}})] in workbook order

Every value is the text the file stores (a number as its digits, a shared
string as its text, an inline string as its text); a date cell is its serial
number as stored, which `serial_date` turns into a day. Formulas keep their
cached result. Nothing is guessed: an empty cell is absent.
"""
import datetime as dt
import io
import re
import zipfile
import xml.etree.ElementTree as ET

M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PR = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_REF = re.compile(r"^([A-Z]+)(\d+)$")


def col_number(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n


def _text(el) -> str:
    return "".join(t.text or "" for t in el.iter(M + "t"))


def sheets(data: bytes) -> list:
    z = zipfile.ZipFile(io.BytesIO(data))
    names = set(z.namelist())
    shared = []
    if "xl/sharedStrings.xml" in names:
        shared = [_text(si) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(M + "si")]
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")).iter(PR + "Relationship")}
    out = []
    for s in ET.fromstring(z.read("xl/workbook.xml")).iter(M + "sheet"):
        target = rels[s.get(R + "id")].lstrip("/")
        path = target if target.startswith("xl/") else "xl/" + target
        rows = {}
        for c in ET.fromstring(z.read(path)).iter(M + "c"):
            m = _REF.match(c.get("r") or "")
            if not m:
                continue
            t = c.get("t")
            if t == "inlineStr":
                v = _text(c)
            else:
                ve = c.find(M + "v")
                if ve is None or ve.text is None:
                    continue
                v = shared[int(ve.text)] if t == "s" else ve.text
            if v == "":
                continue
            rows.setdefault(int(m.group(2)), {})[col_number(m.group(1))] = v
        out.append((s.get("name"), rows))
    return out


def serial_date(v):
    """A spreadsheet day serial (1900 system) as a date, else None."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not 1 < f < 80000:
        return None
    return dt.date(1899, 12, 30) + dt.timedelta(days=int(f))
