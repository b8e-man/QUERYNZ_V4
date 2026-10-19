"""How this lane's documents arrive: case 1 of plan 1.10. The editions of
the Register of Pecuniary and Other Specified Interests of Members of
Parliament (its annual "Summary of annual returns", parliamentary paper
J.7) are held by the old estate under the live old folder's
`var/mp_interests/`, one PDF per edition, 2006 to 2026, downloaded by hand
by Arthur (the old register table records each as "operator-supplied"; no
publisher URL was kept). This lane copies each by hash, read-only, through
the one landing wrapper. Nothing is fetched (step 4.1); the editions are
published on Parliament's site, www3.parliament.nz, under "MPs' financial
interests".

The year in the file name (`mp-<year>.pdf`) is a label; an edition's date
is read from its own title page ("as at 31 January 2018").

    candidate_files()     [(year label, old path)], sorted
    unrecognised()        [file]: a file in the folder no pattern matches
    copy_all(conn)        land everything: [(year label, DocumentRef, old path, new)]
"""
import os
import re

from support.docstore.landing import copy_from_old

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
FOLDER = os.path.join(OLD_LIVE, "var", "mp_interests")
SOURCE = "mp_interests"
_EDITION = re.compile(r"^mp-((?:19|20)\d{2})\.pdf$")


def candidate_files(folder: str = None) -> list:
    folder = folder or FOLDER
    out = []
    for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else ():
        m = _EDITION.match(name)
        if m and os.path.isfile(os.path.join(folder, name)):
            out.append((int(m.group(1)), os.path.join(folder, name)))
    return out


def unrecognised(folder: str = None) -> list:
    folder = folder or FOLDER
    return [n for n in sorted(os.listdir(folder)) if os.path.isdir(folder) and not _EDITION.match(n)] \
        if os.path.isdir(folder) else []


def copy_all(conn, folder: str = None, log=None) -> list:
    out = []
    for year, path in candidate_files(folder):
        ref, new = copy_from_old(path, SOURCE, conn)
        out.append((year, ref, path, new))
        if log:
            log(f"mp_interests: {'landed' if new else 'held'} {year} {ref.sha256[:12]}")
    return out
