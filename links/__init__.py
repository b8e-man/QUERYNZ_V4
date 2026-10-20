"""Links: the three tables, the three verdicts, the two trust settings
(plan 1.9; docs/contracts/links.md); the two confirming rules, the watch,
the old decisions copied and mapped, the test pairs and the six
measurements (plan 4.2 and 4.3).

- links: a pair of rows, the rule, the evidence, a grade (confirmed or near).
- decisions: a remembered ruling on a pair: same, not the same, contested.
  Each says who or what made it and on what evidence. Only ever added to.
- groups: rows gathered into people by following confirmed links, minus
  the decisions. Rebuilt whenever either table changes; edited by nobody.

Two settings are ruled from measurement and have a default until then:
`chain` (follow chains of confirmed links; a flagged group is contested
whole) and `steps` (a connection through more than one person is near,
never confirmed). They are settings, not code.

A row is named `<register>:<key>`: the lane's folder name, a colon, the
published key (card how-links-names-a-register-row; the board reads it
back with `split_ref`). The register and the view are kept apart in
`links.rows` because several views of one register share a key shape.

Pieces: `rows` gathers every person row of every published register under
the one reading of names; `rules` is the two confirming rules, pure;
`build` makes links, groups and the watch; `old` copies the old estate's
ledgers and maps them; `pairs` draws the test pairs; `measure` runs the six
measurements; `review` is the review agent's reading; `check` is the
module's outside check.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TABLES_SQL = os.path.join(HERE, "tables.sql")
PUBLISH_SQL = os.path.join(HERE, "publish.sql")
GRADES = ("confirmed", "near")
VERDICTS = ("same", "not the same", "contested")
MAKERS = re.compile(r"^(review-agent@\d+|correction:\S+|suppression:\S+|old-estate:\S+|person:\S+)$")
SCHEMA = "links"

#: the two trust settings and their defaults (design: "Two settings are ruled from measurement")
SETTINGS = {
    "chain": "follow",            # follow | one-step: how far a chain of confirmed links is trusted
    "contested_group": "whole",   # whole: a group the watch flags is contested as a whole
    "steps": "near",              # near: a multi-step connection through more than one person is near
    "review_applies": "off",      # off | on: whether the review agent's splits become decisions (track C; off until it passes and Arthur rules)
}

#: the name bands, by how many director rows carry the first-and-last name (measurement 1)
BANDS = (("rare", 1, 5), ("middling", 6, 50), ("common", 51, None))


def band_of(n: int) -> str:
    """The band of a first-and-last name carried by `n` director rows."""
    for name, lo, hi in BANDS:
        if n >= lo and (hi is None or n <= hi):
            return name
    return "rare"


def tables_sql() -> str:
    with open(TABLES_SQL, encoding="utf-8") as f:
        return f.read()


def publish_sql() -> str:
    with open(PUBLISH_SQL, encoding="utf-8") as f:
        return f.read()


def ddl(schema: str = SCHEMA) -> str:
    """The tables' SQL for a schema: `links` itself, or a session's scratch schema."""
    if not re.match(r"^[a-z][a-z0-9_]*$", schema):
        raise ValueError(f"not a schema name: {schema!r}")
    return tables_sql().replace("links.", f"{schema}.")


def ensure_schema(conn, schema: str = SCHEMA) -> None:
    """A session's scratch schema is made on first use; `links` itself is
    the database's and is never created here."""
    if not re.match(r"^[a-z][a-z0-9_]*$", schema):
        raise ValueError(f"not a schema name: {schema!r}")
    if schema.startswith("scratch_"):
        from support import db
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        # the session reader sees a scratch schema as it sees every non-private one (support.db.plan_sql)
        conn.execute(f"GRANT USAGE ON SCHEMA {schema} TO {db.ROLES['read']}")
        conn.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO {db.ROLES['read']}")
        conn.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {db.ROLES['read']}")
        conn.commit()


def publish_ddl(schema: str = SCHEMA, pub: str = "pub") -> str:
    """The published views' SQL, for `links` into `pub`, or a scratch schema
    into a scratch `pub` beside it (`<schema>_pub`)."""
    for name in (schema, pub):
        if not re.match(r"^[a-z][a-z0-9_]*$", name):
            raise ValueError(f"not a schema name: {name!r}")
    return publish_sql().replace("links.", f"{schema}.").replace("pub.", f"{pub}.")


def pair(a: str, b: str) -> tuple:
    """The ordered pair the tables store: the smaller key first."""
    if a == b:
        raise ValueError("a link joins two different rows")
    return (a, b) if a < b else (b, a)


def ref(register: str, key: str) -> str:
    return f"{register}:{key}"


def split_ref(r: str) -> tuple:
    register, _, key = r.partition(":")
    return register, key


def check_decision(verdict: str, made_by: str, made_on: dict) -> list:
    out = []
    if verdict not in VERDICTS:
        out.append(f"verdict must be one of {VERDICTS}")
    if not MAKERS.match(made_by or ""):
        out.append("made_by names who or what made it: review-agent@N, correction:ID, suppression:ID, old-estate:ID or person:NAME")
    if not isinstance(made_on, dict) or not made_on:
        out.append("made_on carries the evidence")
    return out
