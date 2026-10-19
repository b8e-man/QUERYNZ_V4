"""The lane's check against the Commission's own figures (plan 4.1, 4.4:
"a figure from outside the estate, the Commission's own published table").

The Commission's listing, "Party donations and loans by year" (the page
`amendments.py` reads), carries under each year from 2017 a "Summary of
donations and loans" table: one row per party, its total party donations
and its total party loans, as the Commission states them. That is the
outside figure. A row is tied to the returns it speaks for by the files
the listing links for that party and year, never by a party name the lane
resolved: from 2022 the table row carries its own links; before that the
year's download list does, and the row is matched to the list item whose
party words are the same (case, macrons, "the", "party", a parenthesis and
"New Zealand"/"NZ" aside). A row matched to no list item is reported,
never guessed.

A party-year is equal when a current return (one no amendment the
Commission states replaces) carries the Commission's donations figure to
the cent. Loans are compared the same way where the return's loans were
read. "NIL" is 0.00; a blank cell is no figure.

    summary(page)                      [Row(year, label, donations, loans, files)], 2017 on
    compare(rows, returns, by_name, replaced, aside)
                                       {"equal", "differ", "loans_differ", "set_aside", "not_held", "not_listed", "unmatched"}
    python -m registers.party_returns.commission [--schema party_returns] [--database querynz_v4]

Read-only.
"""
import html as H
import re
import sys
import unicodedata
from dataclasses import dataclass, field

from registers.party_returns import amendments, capture

SECTION = re.compile(r"<(h[1-6]|button)\b[^>]*>\s*(\d{4})\s+party\s+donations?\s+(?:and\s+loans\s+)?returns\s*</\1>", re.I)
TABLE = re.compile(r"<table\b.*?</table>", re.S | re.I)
CELL = re.compile(r"<t([dh])\b[^>]*>(.*?)</t[dh]>", re.S | re.I)
HREF = re.compile(r"href=\"([^\"]+\.pdf)\"", re.I)
MONEY = re.compile(r"^\$?\s*([\d,]+\.\d{2})$")


@dataclass
class Row:
    year: int
    label: str
    donations: float = None
    loans: float = None
    files: list = field(default_factory=list)      # the Commission's file names for this party-year


def _text(s: str) -> str:
    return " ".join(H.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def figure(cell: str):
    """'$ 1,611,073.77' → 1611073.77; 'NIL'/'Nil' → 0.0; anything else → None."""
    t = cell.strip()
    if t.lower() == "nil":
        return 0.0
    m = MONEY.match(t)
    return float(m.group(1).replace(",", "")) if m else None


def party_words(label: str) -> str:
    """The words a table row and a download link share for one party."""
    t = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"\[.*?\]|\(.*?\)|\*", " ", t)
    t = t.replace("&", " and ").replace("new zealand", "nz").replace("’", "").replace("'", "")
    words = [w for w in re.findall(r"[a-z0-9]+", t) if w not in ("the", "party")]
    return "".join(words)


def summary(page: str, first_year: int = capture.FIRST_YEAR) -> list:
    out = []
    heads = list(SECTION.finditer(page))
    for k, h in enumerate(heads):
        year = int(h.group(2))
        if year < first_year:
            continue
        end = heads[k + 1].start() if k + 1 < len(heads) else len(page)
        t = TABLE.search(page, h.end(), end)
        if not t:
            continue
        rows = re.findall(r"<tr\b.*?</tr>", t.group(0), re.S | re.I)
        header = [_text(c).lower() for _, c in CELL.findall(rows[0])] if rows else []
        try:
            di = next(i for i, c in enumerate(header) if "donations" in c)
            li = next(i for i, c in enumerate(header) if "loans" in c)
        except StopIteration:
            continue
        for r in rows[1:]:
            cells = [c for _, c in CELL.findall(r)]
            if len(cells) <= max(di, li):
                continue
            files = [u.rsplit("/", 1)[-1] for u in HREF.findall(cells[0])]
            label = re.sub(r"\s*[\(\[].*$", "", _text(cells[0])).strip()
            out.append(Row(year, label, figure(_text(cells[di])), figure(_text(cells[li])), files))
    groups = amendments.statements(page)
    for row in out:
        if row.files:
            continue
        same = [g for g in groups if g.year == row.year and party_words(g.party) == party_words(row.label)]
        if len(same) == 1:
            row.files = [l.href.rsplit("/", 1)[-1] for l in same[0].links]
    return out


def _cents(x) -> int:
    return None if x is None else round(float(x) * 100)


def compare(rows: list, returns: list, by_name: dict, replaced: set, aside: dict) -> dict:
    """rows: summary(); returns: dicts with document, year, party_label,
    declared_total, loans_total; by_name: Commission file name (lower) →
    sha256; replaced: shas an amendment the Commission states replaces;
    aside: sha → the stage it was set aside at."""
    ours = {r["document"]: r for r in returns}
    out = {k: [] for k in ("equal", "differ", "loans_differ", "set_aside", "not_held", "not_listed", "unmatched")}
    spoken = set()
    for row in rows:
        if not row.files:
            out["unmatched"].append({"year": row.year, "label": row.label, "donations": row.donations})
            continue
        shas = [s for s in (by_name.get(f.lower()) for f in row.files) if s]
        spoken |= set(shas)
        base = {"year": row.year, "label": row.label, "commission": row.donations}
        if not shas:
            out["not_held"].append({**base, "files": row.files})
            continue
        current = [ours[s] for s in shas if s in ours and s not in replaced]
        if not current:
            out["set_aside"].append({**base, "documents": shas, "stages": sorted({aside.get(s, "no row") for s in shas})})
            continue
        if row.donations is None:
            out["unmatched"].append({**base, "why": "no figure in the Commission's row"})
            continue
        hit = next((r for r in current if _cents(r["declared_total"]) == _cents(row.donations)), None)
        if hit is None:
            out["differ"] += [{**base, "ours": float(r["declared_total"]), "document": r["document"]} for r in current]
            continue
        out["equal"].append({**base, "document": hit["document"]})
        if row.loans is not None and hit.get("loans_total") is not None and _cents(hit["loans_total"]) != _cents(row.loans):
            out["loans_differ"].append({**base, "commission": row.loans, "ours": float(hit["loans_total"]),
                                        "document": hit["document"]})
    for sha, r in ours.items():
        if sha not in spoken and sha not in replaced:
            out["not_listed"].append({"year": r["year"], "label": r["party_label"], "ours": float(r["declared_total"]),
                                      "document": sha})
    return out


def listing() -> str:
    with open(amendments.listing_file(), encoding="utf-8", errors="replace") as f:
        return f.read()


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "party_returns"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        cur = conn.execute(f"SELECT document, year, party_label, declared_total, loans_total FROM {schema}.returns")
        returns = [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        replaced = {r[0] for r in conn.execute(f"SELECT document FROM {schema}.amendments")}
        aside = {r[0]: r[1] for r in conn.execute(f"SELECT document, stage FROM {schema}.set_aside")}
    out = compare(summary(listing()), returns, amendments.held_by_name(capture.old_index()), replaced, aside)
    for k in out:
        print(f"{k}: {len(out[k])}")
    for d in out["differ"]:
        print(f"  DIFFERS {d['label']} {d['year']}: ours {d['ours']:.2f}, Commission {d['commission']:.2f}, document {d['document']}")
    for d in out["loans_differ"]:
        print(f"  LOANS DIFFER {d['label']} {d['year']}: ours {d['ours']:.2f}, Commission {d['commission']:.2f}, document {d['document']}")
    for d in out["unmatched"]:
        print(f"  unmatched: {d}")
    return 1 if out["differ"] or out["loans_differ"] else 0


if __name__ == "__main__":
    sys.exit(main())
