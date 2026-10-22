Number and read back a citation by its row (key with document, page and place), not by a published key: the iwi directory's settlement key names a row per body, so 13 lines cited another body's page and the key-only check passed.
area: scan templates, citations, products/scan, check, registers/iwi_directory, checks that silently pass, keys
paid-for-by: 2026-10-23, scan-templates-2 session, step 6.2 (template 3)

The scan's line builder numbered each citation once per (view, key), the
first row met under a key giving the number and the document for every
later line. Every view the scan had read before keyed one row per key, so
nothing showed. `pub.iwi_directory_settlements` keys the settlement (the
Central North Island collective is one key across 8 bodies), each row read
from its own body's page. The settlement scan gave 282 citations where it
had read 295 rows, and `python -m products.scan check` stayed green: its
read-back asked only whether the key was in the view. It surfaced only from a
count that did not add up (97 settlement refs on 110 lines). Before
trusting a key as a citation, count it against the rows (`group by key having count(*) > 1`); a check that reads back a
citation reads back what the citation says, document and all.
