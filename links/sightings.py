"""Name sightings: every name `pub.names` holds, found in the documents' text by a deterministic pass, before any
model reads them (Arthur, 31 October 2026, 23:40: "do a deterministic pass over the documents checking for the
pub.names before reading the docs with the model").

    python -m links.sightings forms                      # the name forms, from links.rows (pub.names)
    python -m links.sightings scan --lane hansard [--limit N] [--workers 4]
    python -m links.sightings dates                      # each scanned document's own date, where it has none
    python -m links.sightings counts

THE FORMS. One normalised form per way a name of `pub.names` is printed, from a register's filing only (never a name a
text reader's model read: links.rows.MODEL_VIEWS, 1 November 2026): a person's full name as filed (given,
middle, family) and its given-and-family form; an organisation's name as filed. Normalised: macrons folded, lower
case, every run of other than a letter or digit one space. A form of one word, or under MIN_CHARS characters, is
not a form (it finds noise, not a name). `links.name_forms` holds each form with its kind and the count of
`pub.names` rows that print it: the join back to every row (and through its view and key, to where that row is
sighted in its own register) is by `form`.

THE PASS. A document's text is normalised the same way, with every normalised character's place in the original
kept; every run of 2 to MAX_WORDS words is looked up, the longest form at a place wins and the next lookup starts
after it. One row in `links.sightings` per name found: the document (sha256), the lane, the form, the text as the
document prints it, its character offsets, the form's kind. No model; no network; the same text gives the same
rows. `links.sightings_done` records each document scanned under the forms' version, so a run resumes and a
rebuilt form list rescans, and the document's own date (`dated`: a release's publication, a sitting day, a question's
release, a page's archived date, a decision's date; Arthur, 1 November 2026: "add a date to the name sightings. This
is important"). The date is kept once per document, not on each of its sightings; `pub.name_sightings` carries it on
every row by the join on (document, lane, version), the done table's key.

THE LIMITS. A sighting carries the name only, never the text around it, so an address in the text is never copied;
a suppressed or withheld name is a row of `pub.names` with its flag (ruling 142) but never a form. A name that only a document's
address shape carries is a form like any other: the pass records the name and its offsets, never the address.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import unicodedata

from support import db
from links.rows import MODEL_VIEWS

SCHEMA = "links"
MIN_CHARS = 6
MAX_WORDS = 6
LANES = ("beehive", "hansard", "parliament-wayback", "parliament-questions", "courts")

DDL = """
CREATE TABLE IF NOT EXISTS links.name_forms (
    form      text PRIMARY KEY,
    kind      text NOT NULL,
    rows      integer NOT NULL,
    words     smallint NOT NULL
);
CREATE TABLE IF NOT EXISTS links.sightings (
    document  text NOT NULL,
    lane      text NOT NULL,
    form      text NOT NULL,
    printed   text NOT NULL,
    start_at  integer NOT NULL,
    end_at    integer NOT NULL,
    kind      text NOT NULL,
    version   text NOT NULL,
    found_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS sightings_document ON links.sightings (document);
CREATE INDEX IF NOT EXISTS sightings_form ON links.sightings (form);
CREATE TABLE IF NOT EXISTS links.sightings_done (
    document  text NOT NULL,
    lane      text NOT NULL,
    version   text NOT NULL,
    chars     integer NOT NULL,
    found     integer NOT NULL,
    seconds   real NOT NULL,
    done_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (document, lane, version)
);
ALTER TABLE links.sightings_done ADD COLUMN IF NOT EXISTS dated date;
CREATE OR REPLACE VIEW pub.name_sightings AS
    SELECT s.document, s.lane, s.form, s.printed, s.start_at, s.end_at, s.kind, f.rows AS names_rows, s.version, s.found_at,
           d.dated, s.document || '/' || s.lane || '/' || s.start_at AS key
    FROM links.sightings s JOIN links.name_forms f USING (form)
    LEFT JOIN links.sightings_done d ON d.document = s.document AND d.lane = s.lane AND d.version = s.version;
"""


# ── normalising ───────────────────────────────────────────────────────────────────────────────────────────────
def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


_WORD = re.compile(r"[^\W_]+", re.U)


def words_of(text: str) -> list:
    """[(normalised word, start, end)] over the original text: a word is a run of letters or digits; its normal form
    folds macrons and case (a word that folds to nothing is dropped)."""
    out = []
    for m in _WORD.finditer(text or ""):
        w = norm(m.group(0)).replace(" ", "")
        if w:
            out.append((w, m.start(), m.end()))
    return out


#: a form that opens with an article, or is made of these words alone, is a role or a phrase some row filed as a name
#: ("the project", "madam chair", "second respondent", "chief executive", "rt hon"), not a name: measured on the first
#: sample, 31 October 2026, 23:45
ARTICLES = {"the", "a", "an"}
GENERIC = set("""new zealand nz house of representatives select committee madam mr mrs ms miss chair chairperson deputy speaker
rt hon right honourable minister ministers associate prime member members party court courts high supreme district employment
appeal family youth tribunal authority council councils city regional region district crown body corporate second third
respondent respondents applicant applicants appellant appellants plaintiff defendant defendants chief executive officer
director general secretary board trust project fund development government department ministry office commission
commissioner and for to in on at by with j jj cj p""".split())


def generic(form: str) -> bool:
    w = form.split()
    return w[0] in ARTICLES or all(x in GENERIC for x in w)


#: words a register files in front of a person's given names that are a title or an office, not a name ("Dr Andrew West",
#: given "Dr", family "West"; "Judge Gibson"; "Sir Fay"): never the start of a person's form (1 November 2026: 2,312
#: forms opened with one, 145,692 sightings)
TITLES = {"dr", "mr", "mrs", "ms", "miss", "mx", "hon", "rt", "the", "sir", "dame", "judge", "justice", "professor", "prof",
          "rev", "reverend", "father", "cr", "councillor", "lady", "lord", "honourable", "right"}


def forms_of(kind: str, name_filed: str, given: str, middle: str, family: str) -> set:
    out = set()
    if kind == "person" and family:
        g = (given or "").split()           # as filed: "Aiden-Lee" stays one given name, its form "aiden lee johnson"
        while g and norm(g[0]) in TITLES:
            g = g[1:]
        given = " ".join(g)
        out.add(norm(" ".join(x for x in (given, middle, family) if x)))
        if g:
            out.add(norm(f"{g[0]} {family}"))
    else:
        out.add(norm(name_filed))
    return {f for f in out if len(f) >= MIN_CHARS and 2 <= len(f.split()) <= MAX_WORDS and not generic(f)}


#: the scan's rule, part of the version a document is scanned under, so a change of rule rescans every lane.
#: 2 (1 November 2026): a name that overlaps another without lying inside it is kept. Rule 1 took the longest form at
#: each place left to right and skipped past it, so a short form swallowed the start of a real name: "Hon Dr Duncan
#: Webb" gave "dr duncan" (one register row) and never "duncan webb" (6,003 rows).
SCAN_RULE = "2"


def scan(text: str, forms) -> list:
    """[(form, start, end)] for every form found in the text: the longest form at each place, kept unless it lies wholly
    inside a longer one already found (so "michael key" is no sighting inside "john michael key"); two forms that only
    overlap are both kept. In order of place."""
    ws = words_of(text)
    out, n, reach = [], len(ws), -1
    for i in range(n):
        for k in range(min(MAX_WORDS, n - i), 1, -1):
            f = " ".join(w for w, _, _ in ws[i:i + k])
            if f in forms:
                end = ws[i + k - 1][2]
                if end > reach:
                    out.append((f, ws[i][1], end))
                    reach = end
                break
    return out


# ── the forms ─────────────────────────────────────────────────────────────────────────────────────────────────
def build_forms(conn, log=print) -> dict:
    conn.execute(DDL)
    counts, kinds = {}, {}
    t = time.monotonic()
    with conn.cursor(name="forms") as cur:
        cur.itersize = 50000
        # a register's filing only: a name a model read is no form (links.rows.MODEL_VIEWS); a suppressed name is no form either
        # (ruling 142 carries its flag on the row, and a sighting found by its form would carry none)
        cur.execute("SELECT kind, name_filed, given, middle, family FROM links.rows WHERE NOT (view = ANY(%s)) AND NOT suppressed",
                    (sorted(MODEL_VIEWS),))
        for kind, filed, given, middle, family in cur:
            for f in forms_of(kind, filed, given, middle, family):
                counts[f] = counts.get(f, 0) + 1
                kinds.setdefault(f, kind)
    conn.commit()
    conn.execute("DELETE FROM links.name_forms")
    with conn.cursor().copy("COPY links.name_forms (form, kind, rows, words) FROM STDIN") as cp:
        for f, c in counts.items():
            cp.write_row((f, kinds[f], c, len(f.split())))
    conn.commit()
    out = {"forms": len(counts), "seconds": round(time.monotonic() - t, 1),
           "by_kind": {k: sum(1 for f in kinds if kinds[f] == k) for k in set(kinds.values())}}
    log(json.dumps(out))
    return out


def load_forms(conn) -> tuple:
    rows = conn.execute("SELECT form, kind FROM links.name_forms").fetchall()
    forms = {f: k for f, k in rows}
    version = hashlib.sha256((f"scan rule {SCAN_RULE}\n" + "\n".join(sorted(forms))).encode()).hexdigest()[:12]
    return forms, version


# ── the documents' text, by lane ─────────────────────────────────────────────────────────────────────────────
def documents(conn, lane: str) -> list:
    """[(sha256, text getter key)] for the lane's documents, newest first where the lane dates them."""
    q = {
        "beehive": "SELECT document FROM pub.beehive_releases WHERE origin = 'mcp' AND document IS NOT NULL ORDER BY published_on DESC NULLS LAST",
        "hansard": "SELECT document FROM pub.hansard_days WHERE document IS NOT NULL ORDER BY sitting_on DESC",
        "parliament-wayback": "SELECT document FROM pub.parliament_wayback_pages WHERE document IS NOT NULL AND coalesce(text, '') <> '' ORDER BY dated DESC NULLS LAST",
        "parliament-questions": "SELECT document FROM pub.parliament_written_questions WHERE document IS NOT NULL ORDER BY question_released_on DESC NULLS LAST",
        "courts": "SELECT document FROM pub.court_documents WHERE document IS NOT NULL AND coalesce(outcome, '') NOT LIKE 'caught%%' ORDER BY dated DESC NULLS LAST",
    }[lane]
    seen, out = set(), []
    for (d,) in conn.execute(q).fetchall():
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


#: each lane's document date, one per document (the earliest where a register gives one document two)
DATED = {
    "beehive": "SELECT document, min(published_on) AS dated FROM pub.beehive_releases WHERE document IS NOT NULL GROUP BY 1",
    "hansard": "SELECT document, min(sitting_on) AS dated FROM pub.hansard_days WHERE document IS NOT NULL GROUP BY 1",
    "parliament-wayback": "SELECT document, min(dated)::date AS dated FROM pub.parliament_wayback_pages WHERE document IS NOT NULL "
                          "AND dated ~ '^\\d{4}-\\d{2}-\\d{2}$' GROUP BY 1",
    "parliament-questions": "SELECT document, min(question_released_on) AS dated FROM pub.parliament_written_questions "
                            "WHERE document IS NOT NULL GROUP BY 1",
    "courts": "SELECT document, min(dated) AS dated FROM pub.court_documents WHERE document IS NOT NULL GROUP BY 1",
}


def dates_of(conn, lane: str, docs=None) -> dict:
    """{document: date} for the lane, or for `docs` only."""
    if docs is not None:
        docs = list(docs)
        if not docs:
            return {}
        q = f"SELECT * FROM ({DATED[lane]}) x WHERE x.document = ANY(%s)"
        return dict(conn.execute(q, (docs,)).fetchall())
    return dict(conn.execute(DATED[lane]).fetchall())


def date_done(conn, lane: str, log=print) -> int:
    """Fill `dated` on the lane's done rows that have none (the rows scanned before the column; a document whose date its
    register gave later). Returns the rows dated."""
    n = conn.execute(f"UPDATE links.sightings_done d SET dated = x.dated FROM ({DATED[lane]}) x "
                     "WHERE d.document = x.document AND d.lane = %s AND d.dated IS NULL AND x.dated IS NOT NULL", (lane,)).rowcount
    conn.commit()
    log(f"sightings {lane}: {n:,} documents dated")
    return n


def text_of(conn, lane: str, sha: str) -> str:
    from support.docstore.landing import read_bytes
    if lane == "beehive":
        r = json.loads(read_bytes(sha))
        return "\n\n".join(x for x in (r.get("title"), r.get("body_text")) if isinstance(x, str))
    if lane == "hansard":
        return json.loads(read_bytes(sha)).get("text") or ""
    if lane == "parliament-wayback":
        row = conn.execute("SELECT text FROM pub.parliament_wayback_pages WHERE document = %s LIMIT 1", (sha,)).fetchone()
        return (row[0] if row else "") or ""
    if lane == "parliament-questions":
        row = conn.execute("SELECT title, question_text, reply_text FROM pub.parliament_written_questions WHERE document = %s LIMIT 1",
                           (sha,)).fetchone()
        return "\n\n".join(x for x in (row or ()) if x)
    if lane == "courts":
        # the text layer only (a scanned page's reading is the page reader's, not this pass's); a case page's HTML without
        # its tags. links reads no lane's code (imports run one way)
        from support.docread import pages as P
        data = read_bytes(sha)
        if data.startswith(b"%PDF"):
            layer = P.text_pages(data)
            return "\n\n".join(layer[p] for p in sorted(layer))
        import html
        t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", data.decode("utf-8", "replace"))
        return html.unescape(re.sub(r"(?s)<[^>]+>", " ", t))
    raise ValueError(lane)


# ── the pass ──────────────────────────────────────────────────────────────────────────────────────────────────
#: lanes whose text is a column of a published view: read with the document in one streamed query, not looked up one
#: document at a time (the views carry no index on `document`: 31 October 2026, 31 and 223 documents a minute)
STREAMED = {
    "parliament-wayback": "SELECT document, text, CASE WHEN dated ~ '^\\d{4}-\\d{2}-\\d{2}$' THEN dated::date END "
                          "FROM pub.parliament_wayback_pages WHERE document IS NOT NULL AND coalesce(text, '') <> ''",
    "parliament-questions": "SELECT document, concat_ws(E'\\n\\n', title, question_text, reply_text), question_released_on "
                            "FROM pub.parliament_written_questions WHERE document IS NOT NULL",
}


def scan_streamed(lane: str, limit: int = None, log=print, batch: int = 500) -> dict:
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn, db.connect(db.READ_KEY, "querynz_v4") as rconn:
        conn.execute("SET statement_timeout = 0")
        rconn.execute("SET statement_timeout = 0")
        conn.execute(DDL)
        conn.commit()
        forms, version = load_forms(conn)
        done = {d for (d,) in conn.execute("SELECT document FROM links.sightings_done WHERE lane = %s AND version = %s",
                                           (lane, version)).fetchall()}
        log(f"sightings {lane}: {len(forms):,} forms (version {version}), streamed, {len(done):,} done")
        n = found = chars = 0
        t0 = time.monotonic()
        rows, dones = [], []
        with rconn.cursor(name="texts") as cur:
            cur.itersize = 2000
            cur.execute(STREAMED[lane])
            for sha, text, dated in cur:
                if sha in done:
                    continue
                done.add(sha)
                t = time.monotonic()
                text = text or ""
                hits = scan(text, forms)
                rows += [(sha, lane, f, text[a:b], a, b, forms[f], version) for f, a, b in hits]
                dones.append((sha, lane, version, len(text), len(hits), round(time.monotonic() - t, 3), dated))
                n += 1
                found += len(hits)
                chars += len(text)
                if len(dones) >= batch:
                    _write(conn, rows, dones)
                    rows, dones = [], []
                    if n % 10000 < batch:
                        el = time.monotonic() - t0
                        log(f"sightings {lane}: {n:,} documents, {found:,} sightings, {n / el * 60:.0f} documents a minute")
                if limit and n >= limit:
                    break
        _write(conn, rows, dones)
        date_done(conn, lane, log)
        if not limit:
            drop_old(conn, lane, version, log)
        out = {"lane": lane, "documents": n, "sightings": found, "chars": chars, "seconds": round(time.monotonic() - t0, 1),
               "version": version}
        log(json.dumps(out))
        return out


def drop_old(conn, lane: str, version: str, log=print) -> int:
    """A lane's sightings under any other version of the forms: regenerable, removed once the lane is scanned whole under
    this one (the forms changed: the next pass found every name again)."""
    n = conn.execute("DELETE FROM links.sightings WHERE lane = %s AND version <> %s", (lane, version)).rowcount
    conn.execute("DELETE FROM links.sightings_done WHERE lane = %s AND version <> %s", (lane, version))
    conn.commit()
    if n:
        log(f"sightings {lane}: {n:,} sightings under an older version of the forms removed")
    return n


def _write(conn, rows: list, dones: list) -> None:
    with conn.cursor() as cur:
        if rows:
            with cur.copy("COPY links.sightings (document, lane, form, printed, start_at, end_at, kind, version) FROM STDIN") as cp:
                for r in rows:
                    cp.write_row(r)
        if dones:
            cur.executemany("INSERT INTO links.sightings_done (document, lane, version, chars, found, seconds, dated) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", dones)
    conn.commit()


def scan_lane(lane: str, limit: int = None, log=print) -> dict:
    if lane in STREAMED:
        return scan_streamed(lane, limit, log)
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = 0")
        conn.execute(DDL)
        conn.commit()
        forms, version = load_forms(conn)
        done = {d for (d,) in conn.execute("SELECT document FROM links.sightings_done WHERE lane = %s AND version = %s",
                                           (lane, version)).fetchall()}
        docs = [d for d in documents(conn, lane) if d not in done]
        if limit:
            docs = docs[:limit]
        dates = dates_of(conn, lane, docs)
        log(f"sightings {lane}: {len(forms):,} forms (version {version}), {len(docs):,} documents to scan, {len(done):,} done")
        n = found = chars = 0
        t0 = time.monotonic()
        for sha in docs:
            t = time.monotonic()
            try:
                text = text_of(conn, lane, sha)
            except Exception as e:  # noqa: BLE001 — a document that cannot be opened is a line, not a stop
                log(f"sightings {lane}: {sha[:12]} not opened: {type(e).__name__}: {str(e)[:120]}")
                continue
            hits = scan(text, forms)
            with conn.cursor() as cur:
                if hits:
                    with cur.copy("COPY links.sightings (document, lane, form, printed, start_at, end_at, kind, version) FROM STDIN") as cp:
                        for f, a, b in hits:
                            cp.write_row((sha, lane, f, text[a:b], a, b, forms[f], version))
                cur.execute("INSERT INTO links.sightings_done (document, lane, version, chars, found, seconds, dated) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                            (sha, lane, version, len(text), len(hits), round(time.monotonic() - t, 3), dates.get(sha)))
            conn.commit()
            n += 1
            found += len(hits)
            chars += len(text)
            if n % 500 == 0:
                el = time.monotonic() - t0
                log(f"sightings {lane}: {n:,}/{len(docs):,} documents, {found:,} sightings, {chars / el / 1e6:.1f} M chars/s")
        date_done(conn, lane, log)
        if not limit:
            drop_old(conn, lane, version, log)
        out = {"lane": lane, "documents": n, "sightings": found, "chars": chars, "seconds": round(time.monotonic() - t0, 1),
               "version": version}
        log(json.dumps(out))
        return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["forms"]:
        with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
            conn.execute("SET statement_timeout = 0")
            build_forms(conn)
        return 0
    if argv[:1] == ["scan"]:
        lanes = [argv[i + 1] for i, a in enumerate(argv) if a == "--lane"]
        if not lanes or any(x not in LANES for x in lanes):
            print(f"scan takes --lane, one or more of {', '.join(LANES)}", file=sys.stderr)
            return 2
        limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None
        for lane in lanes:
            scan_lane(lane, limit)
        return 0
    if argv[:1] == ["dates"]:
        with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
            conn.execute("SET statement_timeout = 0")
            conn.execute(DDL)
            conn.commit()
            for lane in LANES:
                date_done(conn, lane)
        return 0
    if argv[:1] == ["counts"]:
        with db.connect(db.READ_KEY, "querynz_v4") as conn:
            for r in conn.execute("SELECT lane, count(*), sum(found), sum(chars) FROM links.sightings_done GROUP BY 1 ORDER BY 1").fetchall():
                print(r)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
