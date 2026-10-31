"""The names the deterministic name pass already found in a document (links.sightings, published as
pub.name_sightings), handed to a reader so the model is asked only for the names that pass could not find (Arthur,
1 November 2026). Each found occurrence stays logged in links.sightings with its document, lane and offsets; a reading
records how many names it was given (checks["hint_names"])."""
from support import db

#: the most names one request carries: a long day can hold a thousand sightings; past this the list is cut, longest
#: names first kept (a long name is the least likely to be found again by the model in another form)
MAX_NAMES = 400
HEAD = "NAMES ALREADY FOUND"
RULE = (" The user message may end with a list headed NAMES ALREADY FOUND: names an exact-match pass has already found in "
        "this text. Do not list any name in that list again, nor another form of it (a surname alone, a title and a "
        "surname, initials); list only the people and bodies the text names that the list does not hold. An empty "
        "people list is a correct answer when the list holds every name.")


def sighted(document: str, conn=None) -> list:
    """The distinct printed forms the name pass found in `document`, or [] (no pass yet, or the database out of
    reach: the reader then asks for every name, as before)."""
    try:
        if conn is not None:
            return [r[0] for r in conn.execute("SELECT DISTINCT printed FROM pub.name_sightings WHERE document = %s",
                                               (document,)).fetchall()]
        with db.connect(db.READ_KEY, "querynz_v4") as c:
            c.execute("SET statement_timeout = '30s'")
            return [r[0] for r in c.execute("SELECT DISTINCT printed FROM pub.name_sightings WHERE document = %s",
                                            (document,)).fetchall()]
    except Exception:  # noqa: BLE001 — a hint is help, never a reason for a reading to fail
        return []


def for_text(names, text: str) -> list:
    """The names printed in `text` (this request's own text), longest first, at most MAX_NAMES."""
    got = sorted({n for n in names or () if n and n in (text or "")}, key=lambda n: (-len(n), n))
    return got[:MAX_NAMES]


def block(names) -> str:
    """The list as the user message carries it, or '' when there is none."""
    return f"\n\n{HEAD}\n" + "\n".join(names) if names else ""
