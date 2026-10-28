"""The test pairs of plan 4.3, drawn from the registers; no person labels
them. Each kind states what makes its truth known. At least 200 pairs per
kind per name band where the band can supply them, drawn at random within
the band with a fixed seed; where it cannot, the shortfall is recorded.

    python -m links.pairs [--schema scratch_links] [--seed 43]

Known to be two people:
- `two-directors-one-company`: two director rows with one first and last
  name on one company whose roles stand at once: both in the latest monthly
  file (the lane states no end dates, so a filed window cannot say). A
  register lists one person once per company at a time.
- `two-candidates-one-election`: two candidacies with one name at one
  election in different electorates.

- `donor-and-company-not-live` (ruling 107): a donation row filed under an
  organisation name and a company of that name the register shows was not
  live in the donation's year (registered after its end, or removed before
  its start). A company that did not exist then gave nothing then. Here
  "two people" reads two bodies, the table's word for two entities. The
  company is not a row of `links.rows`, so measurement 3 judges these pairs
  with `rules.sole_company` and the groups, and the review agent, which
  reads people, does not score them (`ORG_KINDS`).

Known to be one person:
- `member-and-candidacy`: a seat and the candidacy the official result says
  won it (the house lane's own join).
- `donor-across-amended-return`: the same donor, by name and amount, in a
  party return and the amendment the Commission says replaces it.

- `candidate-across-amended-return`: the candidate named on an original
  candidate return and on the amendment the Commission's listing says
  replaces it (`pub.candidate_return_totals.replaced_by`, the replacing
  document's hash).
- `donor-across-amended-candidate-return`: the same donor, by name and
  amount, on both.

Not supplied today, and said so: the same role across monthly company
files (the companies lane keeps one row per role across the files, and the
monthly file carries no role identifier); the same charity officer across
returns (the charities register is captured and not yet published).

Bands: by how many director rows carry the first-and-last name (links.BANDS).
"""
from __future__ import annotations

import json
import random
import sys
import time

import links

TARGET = 200
KINDS = {
    "two-directors-one-company": "two people",
    "two-candidates-one-election": "two people",
    "member-and-candidacy": "one person",
    "donor-across-amended-return": "one person",
    "candidate-across-amended-return": "one person",
    "donor-across-amended-candidate-return": "one person",
    "donor-and-company-not-live": "two people",
}
ORG_KINDS = ("donor-and-company-not-live",)    # a donation row and a company entity: not a pair of people rows
NOT_SUPPLIED = {
    "same-role-across-monthly-files": "the companies lane keeps one row per role across the monthly files, and the file carries no role identifier",
    "same-charity-officer-across-returns": "the charities register is captured and not yet published",
}


def candidates_two_directors(conn, s: str) -> list:
    """(row_a, row_b, fl_key, basis) for every pair of director rows with one
    first and last name on one company whose roles stand at once."""
    return conn.execute(f"""
        SELECT least(a.ref, b.ref), greatest(a.ref, b.ref), a.fl_key,
               jsonb_build_object('company', a.entity_ref, 'a', jsonb_build_object('name', a.name_filed, 'from', a.started_on, 'to', a.ended_on),
                                  'b', jsonb_build_object('name', b.name_filed, 'from', b.started_on, 'to', b.ended_on))
        FROM {s}.rows a JOIN {s}.rows b ON b.entity_ref = a.entity_ref AND b.fl_key = a.fl_key AND a.ref < b.ref
        JOIN pub.directors da ON 'companies:' || da.key = a.ref AND da.in_latest
        JOIN pub.directors db ON 'companies:' || db.key = b.ref AND db.in_latest
        WHERE a.view = 'directors' AND b.view = 'directors' AND a.fl_key IS NOT NULL""").fetchall()


def candidates_two_candidates(conn, s: str) -> list:
    return conn.execute(f"""
        SELECT least(a.ref, b.ref), greatest(a.ref, b.ref), a.fl_key,
               jsonb_build_object('election', a.election, 'a', jsonb_build_object('name', a.name_filed, 'electorate', a.electorate),
                                  'b', jsonb_build_object('name', b.name_filed, 'electorate', b.electorate))
        FROM {s}.rows a JOIN {s}.rows b ON b.election = a.election AND b.name_key = a.name_key AND a.ref < b.ref
        WHERE a.view = 'candidates' AND b.view = 'candidates' AND a.electorate IS NOT NULL AND b.electorate IS NOT NULL
          AND a.electorate <> b.electorate""").fetchall()


def candidates_member_candidacy(conn, s: str) -> list:
    return conn.execute("""
        SELECT least('house:' || m.key, 'house:' || m.candidate), greatest('house:' || m.key, 'house:' || m.candidate),
               c.name_key, jsonb_build_object('join', 'pub.members.candidate', 'election', m.election, 'electorate', m.electorate)
        FROM pub.members m JOIN pub.candidates c ON c.key = m.candidate""").fetchall()


def candidates_donor_amended(conn, s: str) -> list:
    return conn.execute(f"""
        SELECT least(a.ref, b.ref), greatest(a.ref, b.ref), a.fl_key,
               jsonb_build_object('original_return', o.key, 'amended_return', o.replaced_by, 'donor', a.name_filed, 'amount', pa.amount)
        FROM pub.party_return_totals o
        JOIN pub.party_return_donors pa ON pa.return_key = o.key
        JOIN pub.party_return_donors pb ON pb.return_key = o.replaced_by AND lower(pb.donor) = lower(pa.donor) AND pb.amount = pa.amount
        JOIN {s}.rows a ON a.ref = 'party_returns:' || pa.key
        JOIN {s}.rows b ON b.ref = 'party_returns:' || pb.key
        WHERE o.replaced_by IS NOT NULL AND a.kind = 'person' AND b.kind = 'person'""").fetchall()


def candidates_candidate_amended(conn, s: str) -> list:
    """The candidate's own row on an original return and on the amendment that replaces it."""
    return conn.execute(f"""
        SELECT least(a.ref, b.ref), greatest(a.ref, b.ref), a.fl_key,
               jsonb_build_object('original_return', o.key, 'amended_return', n.key, 'candidate', a.name_filed, 'year', o.year, 'electorate', o.electorate)
        FROM pub.candidate_return_totals o
        JOIN pub.candidate_return_totals n ON n.key = o.replaced_by || '/declaration'
        JOIN {s}.rows a ON a.ref = 'candidate_returns:' || o.key
        JOIN {s}.rows b ON b.ref = 'candidate_returns:' || n.key
        WHERE o.replaced_by IS NOT NULL""").fetchall()


def candidates_donor_candidate_amended(conn, s: str) -> list:
    return conn.execute(f"""
        SELECT least(a.ref, b.ref), greatest(a.ref, b.ref), a.fl_key,
               jsonb_build_object('original_return', o.key, 'amended_return', n.key, 'donor', a.name_filed, 'amount', pa.amount)
        FROM pub.candidate_return_totals o
        JOIN pub.candidate_return_totals n ON n.key = o.replaced_by || '/declaration'
        JOIN pub.candidate_return_donors pa ON pa.return_key = o.key
        JOIN pub.candidate_return_donors pb ON pb.return_key = n.key AND lower(pb.donor) = lower(pa.donor) AND pb.amount = pa.amount
        JOIN {s}.rows a ON a.ref = 'candidate_returns:' || pa.key
        JOIN {s}.rows b ON b.ref = 'candidate_returns:' || pb.key
        WHERE o.replaced_by IS NOT NULL AND a.kind = 'person' AND b.kind = 'person'""").fetchall()


def candidates_donor_company_not_live(conn, s: str) -> list:
    """A donation row and each company of its name not live in the donation's
    year, as `rules.sole_company` reads live; the band is the donor name's,
    which no director row carries, so rare."""
    from links import rules
    return conn.execute(f"""
        SELECT least(r.ref, o.entity_ref), greatest(r.ref, o.entity_ref), NULL,
               jsonb_build_object('donor', r.name_filed, 'date', r.started_on, 'year', jsonb_build_array(r.started_on, coalesce(r.ended_on, r.started_on)),
                                  'company', o.entity_ref, 'registered_on', o.registered_on, 'removed_on', o.removed_on,
                                  'why', CASE WHEN o.registered_on > coalesce(r.ended_on, r.started_on) THEN 'registered after the year'
                                              ELSE 'removed before the year' END)
        FROM {s}.rows r JOIN {s}.org_names o ON o.org_key = r.name_key
        WHERE r.kind = 'organisation' AND r.register = ANY(%s)
          AND (o.registered_on > coalesce(r.ended_on, r.started_on) OR o.removed_on < r.started_on)""",
                        (list(rules.DONATION_REGISTERS),)).fetchall()


DRAWERS = {
    "two-directors-one-company": candidates_two_directors,
    "two-candidates-one-election": candidates_two_candidates,
    "member-and-candidacy": candidates_member_candidacy,
    "donor-across-amended-return": candidates_donor_amended,
    "candidate-across-amended-return": candidates_candidate_amended,
    "donor-across-amended-candidate-return": candidates_donor_candidate_amended,
    "donor-and-company-not-live": candidates_donor_company_not_live,
}


def name_bands(conn, s: str) -> dict:
    return {fl: links.band_of(n) for fl, n in conn.execute(
        f"SELECT fl_key, count(*) FROM {s}.rows WHERE view = 'directors' AND fl_key IS NOT NULL GROUP BY 1").fetchall()}


def draw(conn, s: str, seed: int = 43, target: int = TARGET, log=print) -> dict:
    """Wipe and redraw `<schema>.test_pairs`. Returns the tally by kind and band, with shortfalls."""
    t0 = time.monotonic()
    bands = name_bands(conn, s)
    conn.execute(f"DELETE FROM {s}.test_pairs")
    tally: dict = {}
    rng = random.Random(seed)
    for kind, drawer in DRAWERS.items():
        truth = KINDS[kind]
        pool: dict = {"rare": [], "middling": [], "common": []}
        for a, b, fl, basis in drawer(conn, s):
            pool[bands.get(fl, "rare")].append((a, b, basis))
        t = tally.setdefault(kind, {"truth": truth, "available": {}, "drawn": {}, "short": {}})
        with conn.cursor() as w:
            for band, items in pool.items():
                items.sort()
                rng.shuffle(items)
                take = items[:target]
                t["available"][band] = len(items)
                t["drawn"][band] = len(take)
                if len(items) < target:
                    t["short"][band] = target - len(items)
                w.executemany(f"""INSERT INTO {s}.test_pairs (kind, truth, band, row_a, row_b, basis, seed)
                                  VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s) ON CONFLICT DO NOTHING""",
                              [(kind, truth, band, a, b, json.dumps(basis, default=str), seed) for a, b, basis in take])
        log(f"links.pairs: {kind}: {t['drawn']} of {t['available']}")
    conn.commit()
    tally["not_supplied"] = NOT_SUPPLIED
    tally["seconds"] = round(time.monotonic() - t0, 1)
    return tally


def main(argv=None) -> int:
    from support import db
    argv = sys.argv[1:] if argv is None else argv
    s = argv[argv.index("--schema") + 1] if "--schema" in argv else links.SCHEMA
    seed = int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 43
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = 0")
        conn.execute(links.ddl(s))
        conn.commit()
        print(json.dumps(draw(conn, s, seed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
