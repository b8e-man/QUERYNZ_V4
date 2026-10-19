"""A workbook's cells as text, row by row, with the standard library only
(the estate carries no spreadsheet package). Shared, inline and plain cells
are read; formulas give their stored value. Rows keep their sheet number,
so a row's place in the workbook is its citation.

    rows(data)     [(sheet row number, [cell text, …])] of the first sheet
"""
import io
import re
import xml.etree.ElementTree as ET
import zipfile

_M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _col(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def rows(data: bytes) -> list:
    z = zipfile.ZipFile(io.BytesIO(data))
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(_M + "si"):
            shared.append("".join(t.text or "" for t in si.iter(_M + "t")))
    sheet = sorted(n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))[0]
    out = []
    for r in ET.fromstring(z.read(sheet)).iter(_M + "row"):
        cells = {}
        for c in r.iter(_M + "c"):
            t, v = c.get("t"), c.find(_M + "v")
            if t == "inlineStr":
                x = "".join(e.text or "" for e in c.iter(_M + "t"))
            elif v is None:
                x = ""
            elif t == "s":
                x = shared[int(v.text)]
            else:
                x = v.text or ""
            cells[_col(c.get("r"))] = x
        width = max(cells) + 1 if cells else 0
        out.append((int(r.get("r")), [cells.get(i, "") for i in range(width)]))
    return out
