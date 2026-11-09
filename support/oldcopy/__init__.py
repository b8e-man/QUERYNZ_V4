"""The old estate's corpora into the new database and store, verbatim (ruling 160, 10 November 2026).

Two copiers, both run by the scheduler at night, both driven by stream I's inventory
(`docs/research/old-estate-inventory.json`, read by `inventory`):

  tables.py   one old table into `old_<database>_private.<table>` (or `<schema>__<table>` when its old schema is not
              `public`): the same columns and types read from the old catalogue, the rows unchanged. In batches by
              key range, each in one repeatable-read snapshot of the source: the batch's rows are counted and hashed
              at the source (md5 over the md5 of each row's text, in key order), streamed by COPY, counted and hashed
              again in the new table inside the same transaction, and committed with its ledger line and the cursor
              only when both agree; a disagreement rolls the rows back, writes a failed ledger line and stops the
              table. A run stops between batches at its budget or at dawn and resumes from the cursor.
  files.py    the old file stores' PDFs and images (an HTML page only where the inventory says its source's rows lost
              the body), each landed into the document store by its bytes (support.docstore.landing.land): a file the
              store already holds adds a name and nothing else, and one already landed under its old path is not
              read again. Batched, resumable from a cursor, every file a ledger line.

Only NEW and PARTLY entries are copied; HELD, DERIVED and OUT never are (`inventory.COPIED`). A PARTLY table copies
only the key ranges the inventory names as missing; a PARTLY table with none named, and a table with no usable key
(a primary key, or a unique index on NOT NULL columns with no expression and no predicate) or a column type the new
database lacks, is refused and the refusal recorded, never guessed.

Limits held here: the old databases are read only through the read-only old login (`db.OLD_READ_KEY`), in read-only
transactions, and nothing is written there (hard limit 22); every query carries a statement timeout; no statement
reads a whole big table (every read is bounded by a key range and LIMIT on the key's index); one batch at a time.
No row's content is printed or logged: the output names tables, counts and hashes only (hard limit 11).

The ledgers live in `oldcopy_private` (tables.sql): never wiped. The copied tables are private by their suffix:
the old databases hold home addresses (hard limit 15; support.db: an address is kept only in a `_private` schema).

    python -m support.oldcopy tables --pieces                 the tables still to copy, one piece key a line
    python -m support.oldcopy tables --piece DB:SCHEMA.TABLE  copy one table until its budget or dawn
    python -m support.oldcopy tables --dry-run --piece KEY    rows and checksum at the source, nothing written
    python -m support.oldcopy files                           the file stores, until the budget or dawn
    python -m support.oldcopy status                          counts from the ledgers

THE INVENTORY'S SHAPE (what `inventory.load` reads; stream I's file):

    {"tables": [{"database": "incoming_news", "schema": "public", "table": "articles", "status": "NEW",
                 "key": ["id"],                                    (optional: names the key; else the catalogue's)
                 "missing": [{"after": null, "through": [1000]}]}],   (PARTLY only: key ranges (after, through])
     "stores": [{"name": "v3-staging", "root": "/abs/path", "status": "NEW", "source": "old-v3-staging",
                 "html": false, "exclude": ["relative/dir"]}]}

`status` may also be spelt `verdict` or `class`; `tables` and `stores` may be lists or objects keyed by name."""
import datetime as dt
import json
import os

LEDGER = "oldcopy_private"
DEST_PREFIX, DEST_SUFFIX = "old_", "_private"
OLD_DATABASES = ("incoming_news", "nzbn_canonical", "extractions")
INVENTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "docs", "research", "old-estate-inventory.json")
HERE = os.path.dirname(os.path.abspath(__file__))

# off-peak: the copy starts no batch outside these local hours (the scheduler's night window's hours, ruling 129;
# the frozen release runs at 06:15 and never waits on this)
WINDOW_START, WINDOW_END, ZONE = "22:00", "05:45", "Pacific/Auckland"


def ledger_sql(ledger: str = LEDGER) -> str:
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        return f.read().replace("{ledger}", ledger)


def ensure_ledger(conn, ledger: str = LEDGER) -> None:
    """The ledger tables, and the schema shut to both readers (a private schema by name)."""
    conn.execute(ledger_sql(ledger))
    conn.execute(f"REVOKE ALL ON SCHEMA {ledger} FROM PUBLIC")


def off_peak(now: dt.datetime = None) -> bool:
    from support.scheduler import night
    w = night.Window(WINDOW_START, WINDOW_END, ZONE, "", "", 0)
    return night.in_window(now or dt.datetime.now(dt.timezone.utc), w)


def keytext(values) -> str:
    """A key bound as stored in the ledger: a JSON list of the key columns' text, or None."""
    return None if values is None else json.dumps([None if v is None else str(v) for v in values])


def keyvalues(text):
    return None if text is None else json.loads(text)
