# The suppressed-names list has no owner in the new estate
kind: finding
state: open
use-case: 1
session: site
opened: 2026-10-20

Hard limit 16: a suppressed name is suppressed on every surface; the row
and the money stay. The old estate holds the list in its database
(`registers.suppressed_names`: two names, both released, none in force
today), applied at the interface by name form (old card C084). The new
estate has no lane and no `pub` view for it. The published-site shape is
built for one: `products/published_site/redact.py` reads the template's
`suppressed_names_view` (`pub.suppressed_names`: name, name_key,
released_at) when the view exists, replaces every matching string in every
payload with `[name suppressed]`, and the `suppressed` gate fails a
version that still shows a form. Today the list is empty and the gate says
so.

A name typed by a person cannot be regenerated, so the list belongs with
the decisions: the links module writes decisions, and a suppression is one
of its three sources (design.md: "the review agent, corrections,
suppressions"). Proposed: `links` publishes `pub.suppressed_names` from a
suppressions table it owns, the two old rows copied across untouched at
the switch. Until then nothing is in force, which matches the old estate.
Blocks nothing before the switch (step 4.8); blocks the switch.
