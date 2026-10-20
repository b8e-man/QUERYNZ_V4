"""How this build's documents arrive: it captures nothing. The pages it reads
are the capture lane's (`registers/charities/capture.py`, case 3 of plan 1.10:
one capture of the register's feed, shared by both builds of the reading so
nothing is fetched twice). The listing is `registers.charities.read.pages`;
the bytes are in the document store by sha256, source `charities`. This
build never opens the feed: the capture lane owns it and its job.

    python -m registers.charities_a.capture      says so, and counts the pages listed for each set
"""
import sys


def main(argv=None) -> int:
    from support import db
    from registers.charities_a import load, read
    print("charities_a: captures nothing; it reads the pages registers/charities landed. Listed:")
    with db.connect(db.READ_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '30s'")
        for s in load.SETS:
            print(f"  {s}: {len(read.listed_pages(conn, s))} page(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
