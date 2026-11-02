# products/archive: history search over Papers Past (use case 16; step 7)

The only reader of `pub.papers_past_items` and `papers_past.items` (tests/test_papers_past_search_only.py holds every other
module off them). It searches; it never mines: it builds no person, claim, link or name row, and nothing it computes is
written into the estate (design, products rule 2). Nothing here is built yet beyond this page; step 8.6 lands the archive's
first batch and measures it (docs/research/papers-past-2026-11-02.md), and steps 7.3 to 7.5 build the keyword index over
whole documents, the meaning index and the search tools on that measurement.

Surface: a web app on its own port, local network only (hard limit 13), when built.
