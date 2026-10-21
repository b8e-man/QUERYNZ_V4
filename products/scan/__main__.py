"""The register scan (plan step 6.1).

  python -m products.scan run NAME [--limit N] [--note TEXT]    run one scan on the real published tables
  python -m products.scan run --stale                            re-run every scan a view has loaded since (and never-run ones)
  python -m products.scan stale                                  which scans are stale, and which views moved
  python -m products.scan export NAME [--run ID] --out DIR      answers.csv, answers.json, citations.csv for the latest (or given) run
  python -m products.scan serve [--bind ADDR] [--port N]        the page, local network only (default 0.0.0.0:8450)
  python -m products.scan state                                  create the scan's tables where QV4_SCAN_STATE points
  python -m products.scan check                                  the outside check against the real published tables
  python -m products.scan templates                              the scans on disk
  python -m products.scan sql NAME                               the query a scan compiles to, under the settings in force
"""
import sys


def _opt(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv or argv[0] not in ("run", "stale", "export", "serve", "state", "check", "templates", "sql"):
        print(__doc__)
        return 2
    cmd = argv.pop(0)
    if cmd == "serve":
        from products.scan import server
        server.serve(_opt(argv, "--bind", server.BIND), int(_opt(argv, "--port", server.PORT)))
        return 0
    if cmd == "state":
        from products.scan import state
        database, schema = state.apply()
        print(f"products.scan: the scan's tables are in {database}.{schema}")
        return 0
    if cmd == "templates":
        from products.scan import template as tpl, plan
        for name, folder in tpl.folders().items():
            t = tpl.load(folder)
            print(f"{name} {t.version}: {t.title}; reads {', '.join(plan.views_read(t))}; {len(t.steps)} steps; {folder}")
        return 0
    if cmd == "sql":
        from products.scan import template as tpl, plan, settings as cfg
        t = tpl.by_name(argv[0])
        for s in t.starts():
            text, params = plan.sql(t, cfg.in_force(), s)
            print(f"-- from pub.{s}; params {params}\n{text};\n")
        return 0
    if cmd == "stale":
        from products.scan import db, run as R
        with db.pub_connect() as pub, db.state_read_connect() as st:
            pub.autocommit = True
            for x in R.stale(pub, st):
                what = "never run" if x["never_run"] else (f"stale: {', '.join(x['stale'])} loaded since run {x['run_id']}" if x["stale"] else f"current (run {x['run_id']})")
                print(f"{x['scan']}: {what}")
        return 0
    if cmd == "run":
        from products.scan import db, run as R, template as tpl
        if "--stale" in argv:
            with db.pub_connect() as pub, db.state_read_connect() as st:
                pub.autocommit = True
                todo = [x["scan"] for x in R.stale(pub, st) if x["stale"] or x["never_run"]]
            print(f"stale: {', '.join(todo) or 'none'}")
            for name in todo:
                R.run(tpl.by_name(name), note="re-run: a view loaded since")
            return 0
        if not argv:
            print("usage: python -m products.scan run NAME [--limit N] [--note TEXT]")
            return 2
        out = R.run(tpl.by_name(argv[0]), limit=int(_opt(argv, "--limit", 0)) or None, note=_opt(argv, "--note", ""))
        return 1 if out["problems"] else 0
    if cmd == "export":
        from products.scan import out as O, template as tpl
        if not argv or "--out" not in argv:
            print("usage: python -m products.scan export NAME [--run ID] --out DIR")
            return 2
        paths = O.export(tpl.by_name(argv[0]), _opt(argv, "--out"), int(_opt(argv, "--run", 0)) or None)
        for p in paths:
            print(p)
        return 0
    from products.scan import check
    return check.main(argv)


if __name__ == "__main__":
    sys.exit(main())
