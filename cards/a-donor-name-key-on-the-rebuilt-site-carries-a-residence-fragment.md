# A donor name key on the rebuilt site carries a residence fragment
kind: blocker
state: closed
use-case: 1
session: comparison-2
opened: 2026-10-20
closed: 2026-10-20

On the rebuilt version 2026-10-20T1513 one donor page's `name_key` (the
links' reading of the filed name, pub.names) and the same key on a party
page's `top_donors` carry a retirement village's name after the donor's
name. A retirement village is where a person lives: hard limit 15, never
shown or extractable. The donor's page and the display name are clean;
the key field is not. party-returns-5 fixed the row (a text cell's name
taken from its first line) on 20 October; the key the links hold was read
before that fix, and the site publishes the key as a field. The words are
not repeated here; the file is `data/donor/hon-robert-smellie-qc-3711a89d.json`
in that version, and the party page is Labour's. The fragment was printed
into this session twice by a sample dump of the page before it was seen.

Which side is right: neither publishes the fragment as a name; the
rebuilt publishes it as a key. Owner: links (re-read the name under the
lane's fixed row) and site (a key is not a field to publish; the
SNAPSHOT's `strings_suppressed` is the place to catch it). Blocks: the
switch and any export; not today's comparison.

Also, 16:20: the frozen site publishes the same fragment as part of a
donor's name: one frozen donor page's file name and the donor picker's
entry for it carry it (the old estate's fold of the filed name), so the
public site shows it today. That is the frozen product, and an emergency
fix there is Arthur's word (hard limit 19). The comparison's records now
withhold any name segment carrying a residence word (`withhold()` in
`checks/comparison.py`), and today's records were rewritten.

Closed on the site's side (site-3, 2026-10-20). A page's key is now the
display name's own form (`paths.name_key`); the links' readings stay inside
the build and no published field repeats one. A ninth gate, `name-keys`,
fails a build on any `name_key` carrying a word the name beside it lacks,
or any name field or file path carrying a residence word (the comparison's
vocabulary, held equal by a test); run on version 2026-10-20T1513 it fails
with 43 faults (14 donor pages, 13 picker rows, 1 home row, party pages'
top donors), naming files and fields and never the text. Measured by code
on a scratch rebuild from the same listing: keys with a word the name lacks
28 → 0 across the five places; residence words in a name field or path
9 → 0 (the interests register's own heading "retirement schemes" and 13
declared positions keep the word, as the register's text, not a name).
The links' half is `the-links-hold-a-donor-key-read-before-party-returns-5-fixed-the-row`.
The frozen site's own copy of the fragment stands until Arthur's word
(hard limit 19); nothing here changes it.

Ruling 77 (21 October): "fix now", first of the two emergency fixes because the exposure is live (hard limit 15). The old estate's fold drops the fragment, the donor page and picker regenerate clean; the patch drafted from the reference copy, the commit Arthur's own; proof is the next daily release.

Applied 22 October, 05:12 (old repository aefd8d0b, 6ff4b228, 7f4a88c6): the frozen page was a 2020 candidate-return row, corrected through the ledger; the 06:19 release is the proof: published 06:29 on 22 October with no residence word in any donor file name or picker entry. The frozen half is closed.
