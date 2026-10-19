"""The older binary workbook (.xls: BIFF8, or BIFF5, inside an OLE2
compound file), read with the standard library alone. The ministers'
releases of 2008 to 2014 come in it. Only what a release table needs is
read: the sheet names, strings, numbers and formulas' cached results.
Formatting, merged ranges and charts are not.

    sheets(data)    [(sheet name, [sheet.Cell…])], worksheets only, in workbook order
"""
import struct

from registers.expenses.sheet import Cell, ref_of

_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_FREE, _END = 0xFFFFFFFF, 0xFFFFFFFE


# ---- the compound file -------------------------------------------------------

def _stream(data: bytes, want=("Workbook", "Book")) -> bytes:
    if data[:8] != _MAGIC:
        raise ValueError("not an OLE2 compound file")
    ssz = 1 << struct.unpack_from("<H", data, 0x1E)[0]
    mssz = 1 << struct.unpack_from("<H", data, 0x20)[0]
    n_fat, first_dir = struct.unpack_from("<II", data, 0x2C)
    cutoff, first_mini, n_mini, first_difat, n_difat = struct.unpack_from("<IIIII", data, 0x38)

    def sector(i: int) -> bytes:
        return data[512 + i * ssz: 512 + (i + 1) * ssz]

    difat = list(struct.unpack_from("<109I", data, 0x4C))
    nxt = first_difat
    for _ in range(n_difat):
        if nxt in (_FREE, _END):
            break
        s = sector(nxt)
        ids = struct.unpack(f"<{ssz // 4}I", s)
        difat += ids[:-1]
        nxt = ids[-1]
    fat = []
    for i in difat[:n_fat]:
        fat += struct.unpack(f"<{ssz // 4}I", sector(i))

    def chain(start: int, table: list) -> list:
        out, seen = [], set()
        while start not in (_FREE, _END) and start < len(table) and start not in seen:
            seen.add(start)
            out.append(start)
            start = table[start]
        return out

    dirs = b"".join(sector(i) for i in chain(first_dir, fat))
    entries = []
    for off in range(0, len(dirs) - 127, 128):
        nlen = struct.unpack_from("<H", dirs, off + 0x40)[0]
        name = dirs[off: off + max(nlen - 2, 0)].decode("utf-16-le", "replace")
        typ = dirs[off + 0x42]
        start, size = struct.unpack_from("<II", dirs, off + 0x74)
        entries.append((name, typ, start, size))
    root = next((e for e in entries if e[1] == 5), None)
    for name, typ, start, size in entries:
        if typ != 2 or name not in want:
            continue
        if size >= cutoff or root is None:
            return b"".join(sector(i) for i in chain(start, fat))[:size]
        minifat = []
        for i in chain(first_mini, fat):
            minifat += struct.unpack(f"<{ssz // 4}I", sector(i))
        ministream = b"".join(sector(i) for i in chain(root[2], fat))
        return b"".join(ministream[i * mssz:(i + 1) * mssz] for i in chain(start, minifat))[:size]
    raise ValueError("no Workbook stream in the compound file")


# ---- records -----------------------------------------------------------------

def _records(wb: bytes, pos: int = 0):
    while pos + 4 <= len(wb):
        rid, ln = struct.unpack_from("<HH", wb, pos)
        yield pos, rid, wb[pos + 4: pos + 4 + ln]
        pos += 4 + ln


def _rk(v: int) -> float:
    if v & 2:
        n = v >> 2
        if n & 0x20000000:
            n -= 0x40000000
        x = float(n)
    else:
        x = struct.unpack("<d", struct.pack("<Q", (v & 0xFFFFFFFC) << 32))[0]
    return x / 100 if v & 1 else x


def _ustr(buf: bytes, pos: int, len_bytes: int = 2) -> tuple:
    """An XLUnicodeString inside one record: (text, new position)."""
    cch = buf[pos] if len_bytes == 1 else struct.unpack_from("<H", buf, pos)[0]
    pos += len_bytes
    flags = buf[pos]
    pos += 1
    runs = ext = 0
    if flags & 8:
        runs = struct.unpack_from("<H", buf, pos)[0]
        pos += 2
    if flags & 4:
        ext = struct.unpack_from("<I", buf, pos)[0]
        pos += 4
    if flags & 1:
        s = buf[pos: pos + 2 * cch].decode("utf-16-le", "replace")
        pos += 2 * cch
    else:
        s = buf[pos: pos + cch].decode("latin-1")
        pos += cch
    return s, pos + 4 * runs + ext


def _sst(parts: list) -> list:
    """The shared strings, read across the SST record and its CONTINUE
    records: a string's characters may break at a record boundary, and the
    piece after it opens with its own one-byte flag (wide or not)."""
    out = []
    pi, buf = 0, parts[0]
    pos = 8
    total = struct.unpack_from("<I", buf, 4)[0]

    def need(p, b, pi_, n):
        # move to the next part when the current one is used up
        while p >= len(b) and pi_ + 1 < len(parts):
            pi_ += 1
            b, p = parts[pi_], 0
        return p, b, pi_

    for _ in range(total):
        pos, buf, pi = need(pos, buf, pi, 3)
        if pos >= len(buf):
            break
        cch = struct.unpack_from("<H", buf, pos)[0]
        flags = buf[pos + 2]
        pos += 3
        runs = ext = 0
        if flags & 8:
            runs = struct.unpack_from("<H", buf, pos)[0]
            pos += 2
        if flags & 4:
            ext = struct.unpack_from("<I", buf, pos)[0]
            pos += 4
        wide, chars, got = flags & 1, [], 0
        while got < cch:
            if pos >= len(buf):
                pi += 1
                if pi >= len(parts):
                    break
                buf, pos = parts[pi], 0
                wide = buf[0] & 1
                pos = 1
            take = min(cch - got, (len(buf) - pos) // (2 if wide else 1))
            if wide:
                chars.append(buf[pos: pos + 2 * take].decode("utf-16-le", "replace"))
                pos += 2 * take
            else:
                chars.append(buf[pos: pos + take].decode("latin-1"))
                pos += take
            got += take
        out.append("".join(chars))
        skip = 4 * runs + ext
        while skip > 0:
            if pos >= len(buf):
                pi += 1
                if pi >= len(parts):
                    break
                buf, pos = parts[pi], 0
            step = min(skip, len(buf) - pos)
            pos += step
            skip -= step
    return out


def _num_text(x: float) -> str:
    return repr(int(x)) if x == int(x) and abs(x) < 1e15 else repr(x)


def sheets(data: bytes) -> list:
    wb = _stream(data)
    biff8 = True
    shared, bounds, sst_parts, in_sst = [], [], None, False
    for pos, rid, body in _records(wb):
        if rid == 0x0809 and pos == 0:
            biff8 = struct.unpack_from("<H", body, 0)[0] == 0x0600
        if rid == 0x0085:                                          # BOUNDSHEET
            off, dt = struct.unpack_from("<I", body, 0)[0], body[5]
            if biff8:
                name, _ = _ustr(body, 6, 1)
            else:
                name = body[7: 7 + body[6]].decode("latin-1")
            bounds.append((off, dt, name))
        elif rid == 0x00FC:                                        # SST
            sst_parts, in_sst = [body], True
            continue
        elif rid == 0x003C and in_sst:                             # CONTINUE of the SST
            sst_parts.append(body)
            continue
        elif rid == 0x000A and sst_parts is not None and in_sst:
            pass
        in_sst = False
        if rid == 0x000A and bounds and pos > bounds[0][0]:
            break
    if sst_parts:
        shared = _sst(sst_parts)
    out = []
    for off, dt, name in bounds:
        if dt != 0:
            continue
        cells, pending = [], None
        for pos, rid, body in _records(wb, off):
            if rid == 0x000A:                                      # EOF of this sheet
                break
            if rid == 0x00FD and len(body) >= 10:                  # LABELSST
                r, c, _, i = struct.unpack_from("<HHHI", body, 0)
                s = shared[i] if i < len(shared) else ""
                cells.append(Cell(ref_of(r + 1, c + 1), r + 1, c + 1, s, s))
            elif rid == 0x0204:                                    # LABEL
                r, c = struct.unpack_from("<HH", body, 0)
                if biff8:
                    s, _ = _ustr(body, 6, 2)
                else:
                    n = struct.unpack_from("<H", body, 6)[0]
                    s = body[8: 8 + n].decode("latin-1")
                cells.append(Cell(ref_of(r + 1, c + 1), r + 1, c + 1, s, s))
            elif rid == 0x0203:                                    # NUMBER
                r, c, _, x = struct.unpack_from("<HHHd", body, 0)
                cells.append(Cell(ref_of(r + 1, c + 1), r + 1, c + 1, x, _num_text(x)))
            elif rid == 0x027E:                                    # RK
                r, c, _, v = struct.unpack_from("<HHHI", body, 0)
                x = _rk(v)
                cells.append(Cell(ref_of(r + 1, c + 1), r + 1, c + 1, x, _num_text(x)))
            elif rid == 0x00BD:                                    # MULRK
                r, c = struct.unpack_from("<HH", body, 0)
                n = (len(body) - 6) // 6
                for k in range(n):
                    _, v = struct.unpack_from("<HI", body, 4 + 6 * k)
                    x = _rk(v)
                    cells.append(Cell(ref_of(r + 1, c + k + 1), r + 1, c + k + 1, x, _num_text(x)))
            elif rid == 0x0006:                                    # FORMULA, its cached result
                r, c = struct.unpack_from("<HH", body, 0)
                res = body[6:14]
                if res[6:8] == b"\xff\xff":
                    if res[0] == 0:
                        pending = (r, c)                           # the text follows in a STRING record
                    elif res[0] == 1:
                        cells.append(Cell(ref_of(r + 1, c + 1), r + 1, c + 1, bool(res[2]), str(bool(res[2])), "="))
                    elif res[0] == 3:
                        cells.append(Cell(ref_of(r + 1, c + 1), r + 1, c + 1, "", "", "="))
                else:
                    x = struct.unpack("<d", res)[0]
                    cells.append(Cell(ref_of(r + 1, c + 1), r + 1, c + 1, x, _num_text(x), "="))
            elif rid == 0x0207 and pending:                        # STRING: a formula's text result
                r, c = pending
                s, _ = _ustr(body, 0, 2) if biff8 else (body[2: 2 + struct.unpack_from("<H", body, 0)[0]].decode("latin-1"), 0)
                cells.append(Cell(ref_of(r + 1, c + 1), r + 1, c + 1, s, s, "="))
                pending = None
        out.append((name, cells))
    return out
