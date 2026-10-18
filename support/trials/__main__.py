"""The trial's command line.

  python -m support.trials piece SHA256       one document through the reader on this card (the scheduler runs it)
  python -m support.trials urgent SHA256 PAGE  one page through the reader on this card (the injected small job, 3.6)
  python -m support.trials rows SHA256        one document's page readings turned into rows by the text reader (3.7)
  python -m support.trials score [--pass P]   score every stored reading per page and write the tables
"""
import sys


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "piece":
        from support.trials import piece
        return piece.main(rest)
    if cmd == "urgent":
        from support.trials import piece
        import json, os
        key = rest[0]
        sha, _, page = key.partition(":")
        page = int(page or (rest[1] if len(rest) > 1 else 1))
        os.environ["QV4_ARGS"] = json.dumps({**json.loads(os.environ.get("QV4_ARGS") or "{}"), "pages": [page], "pass": "urgent"})
        return piece.main([sha])
    if cmd == "rows":
        from support.trials import rows
        return rows.main(rest)
    if cmd == "score":
        from support.trials import score
        return score.main(rest)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
