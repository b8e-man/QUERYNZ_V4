"""The board (plan step 4.9).

  python -m products.board serve [--bind ADDR] [--port N]   the page, on the local network only (default 0.0.0.0:8420)
  python -m products.board state                            create the board's own tables (pins, saved paths) where QV4_BOARD_STATE points
  python -m products.board check [--term NAME]              the outside check against the real published tables (see check.py)
  python -m products.board render "<term>" [view:key …]     the page as HTML on stdout, for a look without a server
"""
import sys


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv or argv[0] not in ("serve", "state", "check", "render"):
        print(__doc__)
        return 2
    cmd = argv.pop(0)
    if cmd == "serve":
        from products.board import server
        bind, port = server.BIND, server.PORT
        if "--bind" in argv:
            bind = argv[argv.index("--bind") + 1]
        if "--port" in argv:
            port = int(argv[argv.index("--port") + 1])
        server.serve(bind, port)
        return 0
    if cmd == "state":
        from products.board import state
        database, schema = state.apply()
        print(f"products.board: pins and paths tables are in {database}.{schema}")
        return 0
    if cmd == "render":
        from products.board import server
        sys.stdout.write(server.render(argv[0] if argv else "", server.parse_path("|".join(argv[1:]))))
        return 0
    from products.board import check
    return check.main(argv)


if __name__ == "__main__":
    sys.exit(main())
