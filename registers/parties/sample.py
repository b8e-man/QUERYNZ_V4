"""The sample filler (plan 1b.6): `fill(conn, schema, items)` loads the
documents named in sample.list into `schema` of the sample database
through this branch's own code. A document not yet in the store is copied
by hash from the old folder; one found in neither fails naming the hash, so
the session can ask for a capture. No model is called.

The lane is small: its sample is the whole of what it reads, the register
page, the applications page, the notices export and the Gazette lane's
export (its register notices read in place; the sample's pub tables hold
no `au` notice, so the listing comes from the document by the same rule).
The labels are those the sample's published tables hold.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`parties_registrations`, …; load.table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore import sha256_file  # noqa: E402
from support.docstore.landing import copy_from_old, land, path_for, read_bytes  # noqa: E402
from registers.parties import capture  # noqa: E402
from registers.parties import load as L  # noqa: E402


def _held(conn, sha: str, name: str, kind: str):
    """Land a stored document under this lane's name; its capture day."""
    if os.path.exists(path_for(sha)):
        ref, _ = land(read_bytes(sha), name=name, source=capture.SOURCE, conn=conn,
                      fetched_at=capture.captured_on(sha) if kind != "notices" else capture.EXPORTED_AT)
        return str(ref.fetched_at)[:10]
    for k, p in capture.candidate_files():
        if sha256_file(p) == sha:
            ref, _ = copy_from_old(p, capture.SOURCE, conn)
            return (capture.captured_on(sha) or ref.fetched_at)[:10]
    raise LookupError(f"parties/sample.list names {sha} ({kind}), which is neither in the document store "
                      f"nor in the old folder: ask for a capture")


def fill(conn, schema: str, items: list) -> int:
    page = export = None
    others = []
    for item in items:
        if item.startswith("key:"):
            continue
        sha = item.split()[0]
        if sha == capture.GAZETTE_EXPORT_SHA:      # the Gazette lane's document: read in place, landed by that lane
            if not os.path.exists(path_for(sha)):
                raise LookupError(f"parties/sample.list names the Gazette lane's export {sha}, not in the document store")
            continue
        if sha == capture.EXPORT_SHA:
            _held(conn, sha, capture.EXPORT_NAME, "notices")
            export = (sha, capture.EXPORT_NAME)
            continue
        data_kind = "register" if page is None and _is_register(sha) else "applications"
        name = next(n for n, k in capture.PAGES.items() if k == data_kind)
        day = _held(conn, sha, name, data_kind)
        if data_kind == "register":
            page = (sha, day, name)
        else:
            others.append((sha, name, data_kind))
    if page is None or export is None:
        raise LookupError("parties/sample.list must name the register page and the notices export")
    return L.build(conn, schema, page, export, others, [], shared=True)["registrations"]


def _is_register(sha: str) -> bool:
    if os.path.exists(path_for(sha)):
        return b"parties__party-info" in read_bytes(sha)
    return any(k == "register" and sha256_file(p) == sha for k, p in capture.candidate_files())
