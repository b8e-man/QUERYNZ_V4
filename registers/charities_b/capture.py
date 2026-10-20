"""How this build's documents arrive: they already have. Case 3 of plan 1.10,
one capture of its own, shared by both builds of the charities reading
(plan step 4.1): `registers/charities/capture.py` fetches the register's open
data feed through the fetch gate and lands every page verbatim by sha256. This
build fetches nothing, imports nothing of that lane (a lane never imports
another), and reads the capture's own listing, `capture_pages`, as the
capture's spec publishes it to the two builds.

The pages a build reads for a set: the newest finished full pass of the set
(mode full, or whole for a set the capture takes in one request), then every
finished changes pass begun after it, oldest first; the same rule as
`registers.charities.read.pages`. When this build is kept it moves into the
capture's folder and this listing becomes that one.
"""
CAPTURE_SCHEMA = "charities"       # the capture lane's schema: its listing, read only


def listing(conn, entity_set: str, schema: str = CAPTURE_SCHEMA) -> list:
    """[(sha256, pass_id, page_no)] of every page read for a set, oldest first."""
    full = conn.execute(f"SELECT pass_id, finished_at FROM {schema}.capture_passes WHERE entity_set = %s "
                        "AND mode IN ('full', 'whole') AND finished_at IS NOT NULL AND pages > 0 "
                        "ORDER BY finished_at DESC LIMIT 1", (entity_set,)).fetchone()
    if full is None:
        return []
    return [tuple(r) for r in conn.execute(
        f"SELECT g.sha256, g.pass_id, g.page_no FROM {schema}.capture_pages g JOIN {schema}.capture_passes p "
        "USING (pass_id) WHERE p.pass_id = %s OR (p.entity_set = %s AND p.mode = 'changes' "
        "AND p.finished_at IS NOT NULL AND p.started_at >= %s) ORDER BY p.pass_id, g.page_no",
        (full[0], entity_set, full[1]))]


def stated(conn, entity_set: str, schema: str = CAPTURE_SCHEMA):
    """(the feed's own count at the start of the set's newest finished full
    pass, rows the pass landed, its start, its end), or None."""
    r = conn.execute(f"SELECT stated, rows_landed, started_at, finished_at FROM {schema}.capture_passes "
                     "WHERE entity_set = %s AND mode IN ('full', 'whole') AND finished_at IS NOT NULL AND pages > 0 "
                     "ORDER BY finished_at DESC LIMIT 1", (entity_set,)).fetchone()
    return tuple(r) if r else None
