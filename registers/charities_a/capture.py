"""How this build's documents arrive: it captures nothing. The pages it reads
are the capture lane's (`registers/charities/capture.py`, case 3 of plan 1.10:
one capture of the register's feed, shared by both builds of the reading so
nothing is fetched twice). The listing is `registers.charities.read.pages`;
the bytes are in the document store by sha256, source `charities`. This
build never opens the feed: the capture lane owns it and its job.

    python -m registers.charities_a.capture      says so, and lists what the capture holds
"""
import sys


def main(argv=None) -> int:
    from registers.charities import read as capture_read
    print("charities_a: captures nothing; it reads the pages registers/charities landed. Held:")
    return capture_read.main(argv)


if __name__ == "__main__":
    sys.exit(main())
