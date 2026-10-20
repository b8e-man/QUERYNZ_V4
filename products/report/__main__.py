"""The subject report (plan step 5.1).

  python -m products.report serve [--bind ADDR] [--port N]       the page, on the local network only (default 0.0.0.0:8440)
  python -m products.report render REF [--template NAME] [--html] [--since YYYY-MM-DD]  one memo on stdout, text by default
  python -m products.report state                               create the saved-reports table where QV4_REPORT_STATE points
  python -m products.report check [--ref REF]                   the outside check against the real published tables
  python -m products.report templates                           the templates on disk
"""
import sys


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv or argv[0] not in ("serve", "render", "state", "check", "templates"):
        print(__doc__)
        return 2
    cmd = argv.pop(0)
    if cmd == "serve":
        from products.report import server
        bind, port = server.BIND, server.PORT
        if "--bind" in argv:
            bind = argv[argv.index("--bind") + 1]
        if "--port" in argv:
            port = int(argv[argv.index("--port") + 1])
        server.serve(bind, port)
        return 0
    if cmd == "state":
        from products.report import state
        database, schema = state.apply()
        print(f"products.report: the saved-reports table is in {database}.{schema}")
        return 0
    if cmd == "templates":
        from products.report import template as tpl
        for name, folder in tpl.folders().items():
            t = tpl.load(folder)
            print(f"{name} {t.version}: {t.title}; {len(t.reads)} views, {len(t.sections)} sections, {len(t.rules)} rules; {folder}")
        return 0
    if cmd == "render":
        from products.report import server
        if not argv:
            print("usage: python -m products.report render REF [--template NAME] [--html]")
            return 2
        ref = argv[0]
        name = argv[argv.index("--template") + 1] if "--template" in argv else "subject"
        since = argv[argv.index("--since") + 1] if "--since" in argv else ""
        ctype, body = server.render(ref, name, "html" if "--html" in argv else "text", since=since)
        sys.stdout.write(body)
        return 0
    from products.report import check
    return check.main(argv)


if __name__ == "__main__":
    sys.exit(main())
