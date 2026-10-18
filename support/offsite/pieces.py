"""What the off-site copy holds, sorted by the delete rule (track B).

Every table of every database named here is copied unless this file says
why it is not. That is the safety property, carried from the old estate's
`ops/backup_classes.py`: a table added next month is copied until somebody
writes down that it can be rebuilt and how. Nothing is left out because it
is big.

Three fates:

  SEND    copied off site; the default for anything not named below.
  LOCAL   can be regenerated but rebuilding costs more than a second disk:
          copied to /mnt/hdd2 only, never sent (the vectors, track B).
  OUT     can be regenerated cheaply by a command that exists; not copied.

A piece is one table (`db:schema.table`) or one file tree (`tree:<name>`).
Each database also carries two small pieces every night, `db:@schema` (the
whole schema, pg_dump --schema-only) and `db:@sequences` (every sequence's
value), so a restore is: schema before data, every table, sequences, schema
after data.

Cadence. A piece is copied whole at the weekly full checkpoint (ruling 21)
and on any night its write counters (or its files) moved. A FROZEN database
is the exception: nothing writes it, so it is copied whole only when it
changed or when its newest full copy is REFRESH_DAYS old, inside the bucket's
45-day retention. The press graph (`extractions`) is frozen: its last
writers stopped on 18 October (step 1.4) and session 1 measured its counters
equal from 21:24 to 06:59. If its counters ever move again it is copied that
night and the record says so."""
import fnmatch
import os

from support import db

SEND, LOCAL, OUT = "send", "local", "out"
FULL_WEEKDAY = 6          # Sunday (Monday is 0): the checkpoint lands before the working week
REFRESH_DAYS = 28         # a frozen piece is sent again before the 45-day bucket rule removes it
OLD_REPO = "/home/user/Git Repos/QueryNZ_V3"   # read only; never written

# database -> the login that reads it, and whether it is frozen. The old
# databases are read through the read-only old login (never the owner).
DATABASES = {
    "querynz_v4": {"login": db.OWNER_KEY, "frozen": False},
    "nzbn_canonical": {"login": db.OLD_READ_KEY, "frozen": False},
    "incoming_news": {"login": db.OLD_READ_KEY, "frozen": False},
    "extractions": {"login": db.OLD_READ_KEY, "frozen": True},
}

# `db.schema.table` patterns (fnmatch) -> (fate, why, the rebuild's path).
# `missing_rebuilds()` checks every named rebuild is on disk.
RULES = {
    "extractions.candidates.*": (OUT, "the candidate register, 120 GB",
        f"{OLD_REPO}/data-layer/candidate_register/candidate_register/cli.py"),
    "extractions.v3.extract_queue": (OUT, "a work queue (extract-queue refills it)", f"{OLD_REPO}/v3/cli.py"),
    "nzbn_canonical.bulk.wikidata_labels": (OUT, "public reference data, fetched again",
        f"{OLD_REPO}/ingestion/wikidata/sync.py"),
    "nzbn_canonical.bulk.wikidata_attrs": (OUT, "public reference data, fetched again",
        f"{OLD_REPO}/ingestion/wikidata/sync.py"),
    "nzbn_canonical.bulk.geonames": (OUT, "public reference data, fetched again",
        f"{OLD_REPO}/ingestion/geonames/sync.py"),
    "nzbn_canonical.bulk.geonames_alternate": (OUT, "public reference data, fetched again",
        f"{OLD_REPO}/ingestion/geonames/sync.py"),
    "incoming_news.public.article_embeddings": (LOCAL,
        "the vectors, 38 GB: days of a graphics card to rebuild, so a second local copy",
        f"{OLD_REPO}/ops/embed_articles.py"),
}

# File trees no database dump covers: name -> (root, fate, why, exclude).
# Paths in `exclude` are relative to the root.
TREES = {
    "qv4-docs": ("/mnt/hdd2/qv4-docs", SEND, "the new document store: captured documents by hash", ()),
    "qv4-live": ("/home/user/querynzv4-work/live", SEND,
                 "stored model readings, run records, check records, the freeze patches",
                 ("llama",)),
    "qv4-inbox": ("/home/user/querynzv4-work/inbox", SEND, "merge requests and notes a session or Arthur typed", ()),
    # The old estate's trees, read only. ec-donations (archive, residue)
    # rejoins: captured documents the old push left out under ruling 198
    # (queue: whether-the-ec-archive-and-residue-join-the-weekly-full-copy,
    # default yes).
    "v3-staging": (f"{OLD_REPO}/var/staging", SEND, "captured documents: the EC forms, party sites, LINZ", ()),
    "v3-audits": (f"{OLD_REPO}/var/audits", SEND, "what every gate and robots read said, when", ()),
    "v3-eras": (f"{OLD_REPO}/var/eras", SEND, "era fire records", ()),
    "v3-review": (f"{OLD_REPO}/var/review", SEND, "what a person wrote: findings and the review ledger",
                  ("docreview/catalogue.jsonl",)),
    "v3-systemd": (f"{OLD_REPO}/ops/systemd", SEND, "the old units, needed before git is cloned", ()),
}


def fate(database: str, schema: str, table: str) -> tuple:
    """(fate, why) for one table; SEND unless a rule names it."""
    key = f"{database}.{schema}.{table}"
    for pat, (f, why, rebuild) in RULES.items():
        if fnmatch.fnmatchcase(key, pat):
            return f, f"{why}; rebuilt by {rebuild}"
    return SEND, "not named as rebuildable, so copied"


def table_piece(database: str, schema: str, table: str) -> str:
    return f"{database}:{schema}.{table}"


def missing_rebuilds(exists=os.path.exists) -> list:
    """OUT and LOCAL rules whose named rebuild is not on disk. A rebuild
    nobody has looked for is no rebuild (the old file caught its own author
    with two invented paths)."""
    return [f"{pat}: no such rebuild {rebuild}" for pat, (_, _, rebuild) in RULES.items()
            if not rebuild or not exists(rebuild)]
