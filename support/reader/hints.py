"""The names the deterministic name pass already found in a document (links.sightings, published as
pub.name_sightings), handed to a reader so the model is asked only for the names that pass could not find (Arthur,
1 November 2026). Each found occurrence stays logged in links.sightings with its document, lane and offsets; a reading
records how many names it was given (checks["hint_names"])."""
from support import db

#: the most names one request carries: a long day can hold a thousand sightings; past this the list is cut, longest
#: names first kept (a long name is the least likely to be found again by the model in another form)
MAX_NAMES = 400
HEAD = "NAMES ALREADY FOUND"
#: from 09:53 to the fix on 1 November 2026 the list was "do not list these again": the model then gave no kind or role for a
#: handed-over name and the name pass records none, so a reading lost "Chris Bishop, minister, Housing Minister"
#: (Arthur: "an unintended negative outcome"). The list is now help against a missed name, never a list to leave out.
RULE = (" The user message may end with a list headed NAMES ALREADY FOUND: names an exact-match pass has found in this "
        "text. The list is help so that no name is missed; it is not a list to leave out. List every name in it that "
        "the text names, each once, with its kind and role by the rules above, as you would if the list were not there; "
        "then list every other person and body the text names that the list does not hold.")
#: a role in words must stand alone (Arthur, 1 November 2026: "administering the Levy" tells nothing, "the levy" is a
#: plain noun, like "looking at the tree"). A person's name is never written into a role: the "of" and "for" fields
#: carry the link, and a name inside a role would escape a court's suppression.
ROLE_WORDS = (" A role written in words must say what it refers to without the rest of the text: where the text calls a "
              "thing by a plain noun (the levy, the scheme, the fund, the contract, the project, the review, the board, "
              "the bill), write what the text says that thing is, in the text's own words, e.g. \"administering the "
              "Infrastructure Funding and Financing levy for the Te Awa Lakes development\", not \"administering the "
              "Levy\". Add nothing the text does not say. Never write a person's name into a role: \"counsel for the "
              "respondent\" stays as written.")


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
