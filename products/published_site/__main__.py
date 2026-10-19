"""The published-site shape's commands (plan 4.4).

  python -m products.published_site build [--listing STAMP] [--out DIR] [--stamp STAMP]
        read the template's pub views, pinned to a frozen release's listing (the newest when none is named),
        write a version folder of the ten kinds, run the gates, record it, stop. No deploy.
  python -m products.published_site preview [--version STAMP] [--out DIR] [--port N] [--bind ADDR]
        serve one version (the newest when none is named) on the local network; never 8300 or 8301
  python -m products.published_site gates [--version STAMP] [--out DIR]
        run the gates again on a written version
  python -m products.published_site plain [--sample SCHEMA]
        the plain page of plan 1.11, from pub.party_return_totals
"""
import os
import sys

from products.published_site import build as B
from products.published_site import gates, preview, version


def arg(argv, name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


def version_dir(argv) -> str:
    out = arg(argv, "--out", B.OUT)
    stamp = arg(argv, "--version")
    d = os.path.join(version.versions_root(out), stamp) if stamp else version.latest(out)
    if not d or not os.path.isdir(d):
        raise SystemExit(f"no version {'named ' + stamp if stamp else 'built yet'} under {out}")
    return d


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    cmd = argv[0] if argv else "build"
    if cmd == "build":
        ok, stamp, _ = B.build(arg(argv, "--listing"), arg(argv, "--out"), stamp=arg(argv, "--stamp"))
        return 0 if ok else 1
    if cmd == "preview":
        preview.serve(version_dir(argv), arg(argv, "--bind", preview.BIND), int(arg(argv, "--port", preview.PORT)))
        return 0
    if cmd == "gates":
        ok = True
        for name, g_ok, line in gates.run_all(version_dir(argv)):
            print(f"  {'PASS' if g_ok else 'FAIL'}  {name:<12} {line}")
            ok = ok and g_ok
        return 0 if ok else 1
    if cmd == "plain":
        from support import db
        from products.published_site import render_party_totals, template
        t = template()
        if "--sample" in argv:
            key, database, table = db.OWNER_KEY, "querynz_v4_sample", f"{arg(argv, '--sample')}.returns"
        else:
            key, database, table = db.PRODUCT_KEY, "querynz_v4", t.reads[0].table
        with db.connect(key, database) as conn:
            cur = conn.execute(f"SELECT * FROM {table} ORDER BY party, year, document")
            rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        sys.stdout.write(render_party_totals(rows, t))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
