# The rebuilt site writes two donor pages for one name
kind: finding
state: closed
use-case: 1
session: comparison-2
opened: 2026-10-20
closed: 2026-10-20

The rebuilt version 2026-10-20T1513 has 60 donor names with two pages
each, one spelling, the second path with the name repeated ("Alan
Wilderland" at `alan-wilderland-1e4e5747` with a 2024 row and at
`alan-wilderland-alan-wilderland-20e57774` with 2025 and 2026; "Andrew
Kelly", "Atlas Concrete Limited", "Oregon Group Limited" likewise). The
frozen site has one page with the whole history, so the matched rebuilt
page is short the rows its twin carries and the twin has no frozen
counterpart. Most are the MPs filed as donors on the 2025 Labour return and
the 2026 declarations of Opportunity Party donors. The comparison's rows
rule names this cause wherever a row the matched page lacks sits on the
twin (`rebuilt-splits-a-donor-across-two-pages`); before, those rows
counted as "rows only one side has" under two lanes' cards.

Which side is right: the frozen one; one donor, one page. The template
settles the page key as the display name, so two keys for one display name
is the site's fold or path rule, not the lanes'. Owner: site.

Also seen: the twin pages carry two different `name_key` values for one
spelling, and the key is the links' reading (pub.names), so the fold that
splits them may be the links' rather than the site's. Owner from here:
site, with links.

Closed (site-3, 2026-10-20). Measured by code on version 2026-10-20T1513:
58 display names with two pages (116 pages). On 54 of them one page's rows
had no reading in `pub.names` at all (rows loaded after the links last ran:
the 2025 Labour return's, the 2026 declarations') and fell under a
filed-spelling stand-in that the site keyed apart from the links' key for
the same spelling; the other 4 had two links keys. `pub.names` itself gives
no filed spelling two keys today (0 of 1,389 rows). Fixed in the shape: a
row the links have not read takes the links' reading of its exact filed
spelling in any register (before, candidate returns only), and after the
fold donors left with one display name are one donor
(`figures.fold_by_display`); the twin-path rule is gone and the build
refuses rather than invent one. Measured against the frozen 2026-10-20T0620,
main's code against this branch's on the same tables:
`rebuilt-splits-a-donor-across-two-pages` 198 → 0; donor pages 990 → 928;
display names with two pages 58 → 0. The rows the links have not read are
on `the-links-hold-a-donor-key-read-before-party-returns-5-fixed-the-row`.
