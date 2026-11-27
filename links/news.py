"""Article → record: each name the news read found, tied to the register entities it is filed as (curation step 2;
Arthur, 26 November 2026; docs/research/curation-plan.md).

    python -m links.news build [--limit N]     both tables again, from every read article's stored reading
    python -m links.news counts

`links.news_entities`: one row per entity a reading names (a person or an organisation; a place is the reading's, not a
register's), with how the article holds it: `mentions` (the forms it used, the name included), `in_headline`, `quoted`
(a speaker of a kept or unjudged quote), `in_role` (holds a role, or is the one a role is of). Its `keys` are the
register keys of its name and each form of two words or more, made by the one reading the registers' rows are keyed by
(links.rows.read_name for a person: the first-and-last and full keys; keys.names.organisation_key for an organisation),
so "Fonterra Co-operative Group Ltd" and "Fonterra Co-operative Group" are one key.

`links.news_ties`: for each article entity, the register entities (`pub.entities.entity_id`: a group, else a lone row)
whose rows carry one of its keys, of the same kind. A row not gathered into a group is no candidate of its own (one
name's ungathered rows are the rows the links could not confirm, never a second person by themselves). One group:
`tied`. Several: `possible`, every candidate a row (decision 1: a possible match is kept out of a feed, listed
apart). No group at all: no row. Sizes never break a tie (ruling: prominence never scores).

Both tables are UNLOGGED and wiped and rebuilt whole (a build makes them again). The readings are opened by key in the
reader store, one read article at a time; the store is never walked.
"""
from __future__ import annotations

import json
import re
import sys
import time

from keys import names as kn

KINDS = ("person", "organisation")
QUOTE_KEYS = ("speaker",)
ROLE_KEYS = ("who", "of")
#: political-office@1 (Arthur, 27 November 2026: twenty cases judged, twenty yes, review set office-rule-1): a role the
#: article itself gives a person that names a political office
OFFICE = re.compile(r"\b(minister|prime minister|mp|member of parliament|leader|co-leader|deputy leader|spokesperson|whip|"
                    r"speaker|mayor|councillor)\b", re.I)
RULE_OFFICE = "political-office@1"

DDL = """
CREATE UNLOGGED TABLE IF NOT EXISTS links.news_entities (
    url_key      text NOT NULL,
    entity       text NOT NULL,          -- the reading's own id, e1 ...
    name         text NOT NULL,
    kind         text NOT NULL,
    keys         text[] NOT NULL,
    mentions     integer NOT NULL,
    in_headline  boolean NOT NULL,
    quoted       boolean NOT NULL,
    in_role      boolean NOT NULL,
    published_at timestamptz,
    PRIMARY KEY (url_key, entity)
);
ALTER TABLE links.news_entities ADD COLUMN IF NOT EXISTS office boolean NOT NULL DEFAULT false;   -- a political office the article gives it
CREATE UNLOGGED TABLE IF NOT EXISTS links.news_ties (
    url_key      text NOT NULL,
    entity       text NOT NULL,
    entity_id    text NOT NULL,          -- pub.entities.entity_id
    status       text NOT NULL,          -- tied | possible
    candidates   integer NOT NULL,
    PRIMARY KEY (url_key, entity, entity_id)
);
-- the rule that decided: name (one group of the name: tied; several: possible), or political-office@1 (a possible name
-- whose one politician the article's office settles: tied, the other candidates "passed over")
ALTER TABLE links.news_ties ADD COLUMN IF NOT EXISTS rule text NOT NULL DEFAULT 'name';
CREATE INDEX IF NOT EXISTS news_ties_entity_id ON links.news_ties (entity_id);
CREATE UNLOGGED TABLE IF NOT EXISTS links.news_subjects (
    url_key      text NOT NULL,
    subject      text NOT NULL,          -- folded (registers.news.subjects.fold): one subject however it is cased
    said         text NOT NULL,          -- as the reading names it
    broad        boolean NOT NULL,       -- an IPTC label (article.themes), not a specific subject
    PRIMARY KEY (url_key, subject)
);
CREATE INDEX IF NOT EXISTS news_subjects_subject ON links.news_subjects (subject);
CREATE UNLOGGED TABLE IF NOT EXISTS links.news_articles (
    url_key      text PRIMARY KEY,
    host         text,
    form         text,                   -- the reading's article.type: news, opinion, feature ... (decision 19)
    published_at timestamptz
);
"""

PUBLISH = """
CREATE OR REPLACE VIEW pub.news_entities AS SELECT * FROM links.news_entities;
CREATE OR REPLACE VIEW pub.news_ties AS SELECT * FROM links.news_ties;
CREATE OR REPLACE VIEW pub.news_subjects AS SELECT * FROM links.news_subjects;
CREATE OR REPLACE VIEW pub.news_articles AS SELECT * FROM links.news_articles;
"""


def keys_of(name: str, kind: str, forms=()) -> list[str]:
    from links.rows import read_name
    out = []
    for n in [name, *forms]:
        n = (n or "").strip()
        if len(n.split()) < 2 and not (kind == "organisation" and n == (name or "").strip()):
            continue                                   # one word ("Hipkins") is no key; an organisation's own name is
        if kind == "person":
            r = read_name(n)
            ks = [r["fl_key"], r["full_key"]]
        else:
            ks = [kn.organisation_key(n)]
        for k in ks:
            if k and k not in out:
                out.append(k)
    return out


def entities_of(got: dict, title: str) -> list[dict]:
    """The reading's people and organisations with how the article holds each."""
    ents = got.get("entities") if isinstance(got.get("entities"), dict) else {}
    quoted = {q.get(k) for q in got.get("quotes") or [] if isinstance(q, dict) for k in QUOTE_KEYS}
    roles = {r.get(k) for r in got.get("roles") or [] if isinstance(r, dict) for k in ROLE_KEYS}
    offices = {r.get("who") for r in got.get("roles") or [] if isinstance(r, dict) and OFFICE.search(r.get("role") or "")}
    head = (title or "").lower()
    out = []
    for eid, e in ents.items():
        e = e or {}
        name, kind = (e.get("name") or "").strip(), e.get("kind")
        if not name or kind not in KINDS:
            continue
        forms = [f for f in (e.get("forms") or []) if isinstance(f, str)]
        keys = keys_of(name, kind, forms)
        if not keys:
            continue
        out.append({"entity": eid, "name": name, "kind": kind, "keys": keys, "mentions": len(set(forms) | {name}),
                    "in_headline": any(f.lower() in head for f in set(forms) | {name} if len(f) > 3),
                    "quoted": eid in quoted, "in_role": eid in roles, "office": kind == "person" and eid in offices})
    return out


def fold(s: str) -> str:
    import re
    import unicodedata
    s = "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def subjects_of(url_key: str, got: dict) -> list[tuple]:
    """[(url_key, folded, as said, broad)]: the specific subjects (a reader from 6 on) and the broad (article.themes)."""
    out, seen = [], set()
    spec = [(s.get("name") if isinstance(s, dict) else s, False) for s in got.get("subjects") or []]
    broad = [(t, True) for t in ((got.get("article") or {}).get("themes") or [])]
    for said, b in spec + broad:
        said = (said or "").strip() if isinstance(said, str) else ""
        f = fold(said)
        if f and f not in seen:
            seen.add(f)
            out.append((url_key, f, said, b))
    return out


def office_rule(conn) -> int:
    """political-office@1 over the possible ties: a person the article gives a political office, of whose candidates
    exactly one is a politician (pub.entities.politician), is that politician. Returns the names it settled."""
    conn.execute("""
        CREATE TEMP TABLE office_settled ON COMMIT DROP AS
        SELECT t.url_key, t.entity
        FROM links.news_ties t JOIN links.news_entities n USING (url_key, entity) JOIN pub.entities e USING (entity_id)
        WHERE t.status = 'possible' AND n.kind = 'person' AND n.office
        GROUP BY 1, 2 HAVING sum(coalesce(e.politician, false)::int) = 1""")
    conn.execute("""
        UPDATE links.news_ties t SET status = CASE WHEN coalesce(e.politician, false) THEN 'tied' ELSE 'passed over' END,
                                     rule = %s
        FROM office_settled o, pub.entities e
        WHERE t.url_key = o.url_key AND t.entity = o.entity AND e.entity_id = t.entity_id""", (RULE_OFFICE,))
    return conn.execute("SELECT count(*) FROM office_settled").fetchone()[0]


def build(limit: int = None, log=print) -> dict:
    from support import db
    from support import reader as rd
    t0 = time.monotonic()
    store = rd.Store()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = 0")
        conn.execute(DDL)
        for t in ("news_ties", "news_entities", "news_subjects", "news_articles"):
            conn.execute(f"DELETE FROM links.{t}")
        arts = conn.execute("SELECT url_key, reading_key, title, published_at, host, subjects_key FROM pub.news_read WHERE outcome IN ('read', 'replayed') "
                            "ORDER BY read_at DESC" + (f" LIMIT {int(limit)}" if limit else "")).fetchall()
        rows, subj, art, missing = [], [], [], 0
        for url_key, key, title, published, host, subjects_key in arts:
            try:
                got = json.loads(store.get(key).text or "null") or {}
            except Exception:
                missing += 1
                continue
            if not got.get("subjects") and subjects_key:     # read before reader 6: its subjects pass's own reading
                try:
                    got["subjects"] = (json.loads(store.get(subjects_key).text or "{}") or {}).get("subjects") or []
                except Exception:
                    pass
            for e in entities_of(got, title):
                rows.append((url_key, e["entity"], e["name"], e["kind"], e["keys"], e["mentions"], e["in_headline"],
                             e["quoted"], e["in_role"], published, e["office"]))
            subj += subjects_of(url_key, got)
            art.append((url_key, host, ((got.get("article") or {}).get("type") or None), published))
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO links.news_entities (url_key, entity, name, kind, keys, mentions, in_headline, quoted, "
                            "in_role, published_at, office) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                            "ON CONFLICT DO NOTHING", rows)
            cur.executemany("INSERT INTO links.news_subjects VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", subj)
            cur.executemany("INSERT INTO links.news_articles VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", art)
        log(f"news entities: {len(rows):,} from {len(arts) - missing:,} readings ({missing} not in the store), "
            f"{time.monotonic() - t0:.0f} s")
        # each key, its groups of the same kind (a person by its first-and-last or full key, an organisation by its name key)
        conn.execute("""
            CREATE TEMP TABLE nk AS
            SELECT DISTINCT unnest(keys) AS key, kind FROM links.news_entities;
            CREATE INDEX ON nk (key);
            ANALYZE nk;
            CREATE TEMP TABLE kg AS
            SELECT nk.key, nk.kind, g.group_id::text AS entity_id
            FROM nk JOIN links.rows r ON r.kind = nk.kind AND nk.kind = 'person' AND r.fl_key = nk.key
            JOIN pub.groups g ON g.row_key = r.ref
            UNION
            SELECT nk.key, nk.kind, g.group_id::text
            FROM nk JOIN links.rows r ON r.kind = nk.kind AND nk.kind = 'person' AND r.full_key = nk.key
            JOIN pub.groups g ON g.row_key = r.ref
            UNION
            SELECT nk.key, nk.kind, g.group_id::text
            FROM nk JOIN links.rows r ON r.kind = nk.kind AND nk.kind = 'organisation' AND r.name_key = nk.key
            JOIN pub.groups g ON g.row_key = r.ref;
            INSERT INTO links.news_ties (url_key, entity, entity_id, status, candidates)
            SELECT url_key, entity, entity_id, CASE WHEN n = 1 THEN 'tied' ELSE 'possible' END, n
            FROM (SELECT url_key, entity, entity_id, count(*) OVER (PARTITION BY url_key, entity) AS n
                  FROM (SELECT DISTINCT e.url_key, e.entity, kg.entity_id
                        FROM links.news_entities e CROSS JOIN LATERAL unnest(e.keys) k(key)
                        JOIN kg ON kg.key = k.key AND kg.kind = e.kind) d) x;
        """)
        out_office = office_rule(conn)
        conn.execute(PUBLISH)
        out = dict(zip(("tied", "possible"), conn.execute(
            "SELECT count(DISTINCT (url_key, entity)) FILTER (WHERE status = 'tied'), "
            "count(DISTINCT (url_key, entity)) FILTER (WHERE status = 'possible') FROM links.news_ties").fetchone()))
        conn.commit()
    out["political_office"] = out_office
    out.update({"entities": len(rows), "articles": len(arts) - missing, "seconds": round(time.monotonic() - t0, 1)})
    log(json.dumps(out))
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["build"]:
        build(int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
