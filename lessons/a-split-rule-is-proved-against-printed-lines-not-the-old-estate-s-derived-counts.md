A split rule is proved against the source's printed speaker lines, not the old estate's derived counts: the old Hansard lists held 2 of a third reading's 20 speakers, so agreeing with them was the wrong target.
area: registers/hansard, split rule, old estate, proof, deterministic reading

**What happened (hansard-3, 31 October 2026).** The brief asked that the split of a sitting day's text into sections
and speaker turns be proved on the 137 days both the MCP and the old estate hold, against the sitting rows' own
counts. The first comparison showed the split finding more member turns than the old lists on 128 of 137 days, which
looked like over-splitting. Listing one section side by side showed the opposite: the old estate's speaker list for the
Citizenship (Western Samoa) (Restoration) Amendment Bill's third reading (20 November 2024, 91,000 characters) named
two speakers; the printed text has twenty, each a paragraph opening `NAME (Party—Electorate):`. On oral questions the
old lists skip the question line and often the first answer (+1 on 432 matched sections, +2 on 278). The 8 days where
the split found fewer were the urgency sittings whose later calendar days the MCP lacks (the known card).

**The rule.** When the old figure is itself a derivation (a scrape's speaker list, a model's count), read a few of the
differing sections against the source's own printed lines before tuning the rule toward the old figure. Record the
direction and the reason per class of difference; keep the comparison as a counted, never failed, line of the check so
a change in the rule shows up, and let the printed lines be the ground truth.

**How to apply.** `python -m registers.hansard.split --prove` prints the day table, the per-section histogram by
subject and the unmatched speakers; `check.py` carries the day counts under "the split". A heading or speaker shape
the rule misses (a wrapped heading at indent 1, a numbered question line `1. NAME … to the Minister:`, a three-word
surname) shows as a run of sections or days off by the same amount: fix the shape, not the threshold.
