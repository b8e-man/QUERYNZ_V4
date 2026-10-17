# Contract: links, decisions, groups

**Fixes:** the three table shapes, the three verdicts, who or what makes a
decision, the two trust settings. **Test:** `links/tests/` (the DDL
applies to the sample database). **Taken from:** the old estate's ledgers
of judgments (`donor_anchors`, `roster_folds`, `review_verdicts`), re-keyed
to rule and evidence; the hand-set weights are not taken.

1. **There is no stored person.** A person is what you get by reading the
   three tables together.
2. **Links** (`links.links`): a pair of register rows, the rule that joined
   them (by name and version), the evidence, and a grade: `confirmed` or
   `near`, with the reason it is only near. Rebuilt by the rules on every
   rebuild. The pair is stored smaller key first, once.
3. **Decisions** (`links.decisions`): a remembered ruling on a pair, one of
   `same`, `not the same`, `contested` (the link drops to near). Each says
   who or what made it (`review-agent@N`, `correction:ID`, `suppression:ID`,
   `old-estate:ID`, `person:NAME`) and on what evidence. **Only ever added
   to**: a trigger refuses UPDATE and DELETE.
4. **Groups** (`links.groups`): rows gathered into people by following
   confirmed links, minus the decisions; a group the watch flags is
   contested as a whole. Rebuilt whenever either table changes; edited by
   nobody. Each build records the settings it ran with.
5. **The old decisions** are copied exactly as they were into
   `links.old_decisions`, never edited, and mapped to the new stable keys
   by content (the old row numbers changed nightly).
6. **Two settings, defaults until Arthur rules from measurement:** `chain`
   (follow chains of confirmed links) and `steps` (a connection through
   more than one person is near, never confirmed). Settings, not code.
7. **The rules** (what confirms, what is near, the watch, the review agent)
   are step 4.2 and track C; they read this contract and change it only by
   ruling. Organisations with an official number need none of this: the
   number is the link.
