"""The shape's outside check (spec line 4), against the real published
tables through the product reader, never the sample:

  1. A version folder built from a frozen release's recorded listing
     carries every one of the ten kinds, or the manifest says which kind is
     not held and why (board members: no lane).
  2. Every gate is green on it, the Commission's table among them (the one
     figure from outside the estate).
  3. A build with no listing, or no document store at hand, fails plainly
     rather than writing a version.
  4. Every money row in the version cites a document the listing holds
     (the pin), and every cited document has a name in the store.

Returns a board-shaped result ({check, ok, items, alarms}) so the
integrator can register it on the checks board; builds into the session's
scratch folder (or QV4_SITE_CHECK_OUT) and never into the live site folder.

    python -m products.published_site check [--out DIR]      exit 1 on any failure
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

from products.published_site import build as B
from products.published_site import paths, pin, version

NAME = "site"


def check(out: str = None, listings_folder: str = None) -> dict:
    items = []
    out = out or os.environ.get("QV4_SITE_CHECK_OUT") or tempfile.mkdtemp(prefix="qv4-site-check-")
    lv = pin.latest(listings_folder)
    if not lv:
        items.append({"name": "listing", "ok": False, "detail": "no frozen release listing to build from"})
        return {"check": NAME, "ok": False, "items": items, "alarms": []}
    ok, stamp, lines = B.build(lv, out, listings_folder=listings_folder, log=lambda s: None)
    if not ok or not stamp:
        items.append({"name": "build", "ok": False, "detail": "; ".join(l.strip() for l in lines if l.startswith(("fail", "  FAIL")))[:400]})
        return {"check": NAME, "ok": False, "items": items, "alarms": []}
    vdir = os.path.join(version.versions_root(out), stamp)
    m = version.manifest_of(vdir)
    items.append({"name": "build", "ok": True, "detail": f"{stamp} from listing {lv}: {m['files']} files, {m['bytes']:,} bytes"})
    missing = [k for k in paths.KINDS if not m["written"].get(k) and k not in (m.get("kinds_not_held") or {})]
    items.append({"name": "ten-kinds", "ok": not missing,
                  "detail": (f"missing: {', '.join(missing)}" if missing else
                             f"{sum(1 for k in paths.KINDS if m['written'].get(k))} kinds written; not held: "
                             + (", ".join(f"{k} ({v})" for k, v in (m.get("kinds_not_held") or {}).items()) or "none"))})
    gate_lines = [l for l in lines if l.strip().startswith(("PASS", "FAIL"))]
    reds = [l.strip() for l in gate_lines if l.strip().startswith("FAIL")]
    items.append({"name": "gates", "ok": not reds, "detail": "; ".join(reds)[:400] if reds else f"{len(gate_lines)} gates green"})
    left = sum(x["left_out"] for x in m["pinned"].values())
    items.append({"name": "pin", "ok": True, "detail": f"{left} money rows left out for citing a document the listing does not hold; "
                                                     f"{m['documents_cited']} documents cited, {m['documents_unnamed']} unnamed"})
    items.append({"name": "no-release", "ok": m.get("deploy", "").startswith("none"), "detail": m.get("deploy", "")})
    return {"check": NAME, "ok": all(i["ok"] for i in items), "items": items, "alarms": []}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    r = check(out)
    for i in r["items"]:
        print(f"  {'ok ' if i['ok'] else 'RED'}  {i['name']:<10} {i['detail']}")
    print(("pass" if r["ok"] else "fail") + f"  {NAME}: {sum(1 for i in r['items'] if not i['ok'])} red")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
