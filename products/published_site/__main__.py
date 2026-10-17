"""Print the plain page (plan 1.11).

  python -m products.published_site                       from pub.party_return_totals in querynz_v4, as the product reader
  python -m products.published_site --sample SCHEMA       from a scratch schema of the sample database (building only)
"""
import sys

from support import db
from products.published_site import render_party_totals, template


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    t = template()
    if "--sample" in argv:
        schema = argv[argv.index("--sample") + 1]
        key, database, table = db.OWNER_KEY, "querynz_v4_sample", f"{schema}.returns"
    else:
        key, database, table = db.PRODUCT_KEY, "querynz_v4", t.reads[0].table
    with db.connect(key, database) as conn:
        cur = conn.execute(f"SELECT * FROM {table} ORDER BY party, year, document")
        rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur]
    sys.stdout.write(render_party_totals(rows, t))
    return 0


if __name__ == "__main__":
    sys.exit(main())
