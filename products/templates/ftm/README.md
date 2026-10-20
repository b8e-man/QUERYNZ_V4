# The Follow the Money template (plan 4.4)

One template per use case; this is Follow the Money's. `ftm.json` is read as data by `products/published_site/site_template.py` and held to the template contract by `products/templates/__init__.py`; its own tests are in `tests/`.

What it holds:

- `reads`: the 26 `pub` views the build may read, each with licence, attribution and refresh. `Tables.get` refuses any other view, so the list is the whole of what the site reads.
- `sections`: the ten kinds of published file, in order.
- `rules`: the thirteen rules the plan fixes (the window, the races, the EC-filed donor, the return as the record, no press, no home address, a suppressed name suppressed).
- `settings`: the frozen site's (window 2017, races 2020/2023/2026, seven headline parties by registration key, the $15,000 line, the disclosure regimes, the donor list cut).
- `settled`: the choices the comparison found open, each with which side's rule the template takes and why: the donor picker, the donor display name, the donor and person page keys, the party page key.
- `page_sections`: every frozen section the pages carry, by kind; the person-page sections the queue item `which-frozen-sections-belong-in-the-follow-the-money-template` would move to step 5 are marked and leave by that ruling alone.
- `sections_added`: the keys only the rebuilt pages carry, for the comparison's section rule.
- `known_limits`: the page a reader sees, starting "Nothing before 2017".

Version 2 (site-2, 2026-10-20): candidate returns, the interests register, financial statements and every frozen money section read and rendered.

Version 3 (site-3, 2026-10-20): the donor page key is the display name's own form and repeats no reading of the links; one display name is one donor; a declaration's year is the gift's (`settled.declaration_year`); a statement is one line however many files.
