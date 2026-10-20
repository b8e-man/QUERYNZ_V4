# A donor name key on the rebuilt site carries a residence fragment
kind: blocker
state: open
use-case: 1
session: comparison-2
opened: 2026-10-20

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
