# parties-2: the register's notices from the Gazette lane, the party labels view
branch: session/parties-2 (pushed; 18637c3, main merged in at cec4194)
session: parties-2 (Opus, build)
raised: 2026-10-20
claims: registers/parties/ (new `labels.py`, `profile-proposed.jsonl`; capture, read, notices, load, check, sample, tables, publish, spec, pane, sample.list, tests); cards closed `a-renamed-party-s-public-money-is-summed-under-one-name`, `two-registrations-share-one-party-name`, `the-parties-lane-joins-labels-the-frozen-site-left-unfolded`; annotated `three-party-labels-resolve-to-no-registration`, `short-party-labels-in-the-expense-and-interests-registers-do-not-resolve`, `an-unregistered-party-label-is-not-on-the-rebuilt-candidacy`, `six-parties-are-off-the-register-with-no-cancellation-held`; opened `the-lanes-and-the-site-do-not-yet-join-the-party-labels`; lesson `a-one-off-export-chosen-by-the-old-classifier-misses-what-it-mistyped`; docs/status/parties.md

Step 4.1, tranche 2. Fetches nothing.

**Notices from the Gazette lane.** The register's notices are the Gazette
lane's rows in `pub.gazette_notices`, section `au`, titled as the
register's (`capture.TITLE_RULE`): 137. Each is read from that lane's
export by hash (sha256 47de7e09…), imported nothing of that lane's, where
its text equals the parties export's after the reader's normalising (136
of 136); a different text would keep the export's and be a catch-log line
(none). Rows cite that document, the notice and resolution, and the
notice's row there (`pub.party_events.gazette_key`). The parties export
stays landed, listed "read, compared, not cited". The one new notice,
2023-au2700, cancels Heartland New Zealand on 20 June 2023. Where the
database publishes no `au` row (the shared sample), the listing is read
from the same document by the same rule (137, equal).

**A reading fault fixed.** "cancel the registration of the One New
Zealand Party logo" (2011-au5154, section 70A) was read as the party's
cancellation and minted a second registration; it is a logo resolution
now. Reader `registers.parties.notices 2`; profile
`gazette-party-register-notices` version 2 proposed (append it from
`registers/parties/profile-proposed.jsonl`). 78 → 77 registrations; the
key `ec-party/before-2000/be7ccc2c63e1/2` is gone (no lane references it).

**Two registrations of one name.** `pub.parties.same_name_as` and
`same_name_note` (new columns, inserted before `read_from`): New Zealand
Loyal (2023–2024, 2026–), United Future New Zealand (2001–2013,
2013–2018), never joined.

**`pub.party_labels`** (new table `parties.labels`). Every distinct
(label, on) 17 tables of six lanes publish (party returns, disclosures,
candidate returns, house, expenses, interests, party finance), `on` the
filing's day or its year, joined to the registration live then through
`keys.parties.party_name` over this load's own names; plus the bracket
rule party-finance uses, and Independent/IND as not a party. Unresolved
rows say why; `same_name` names both registrations where two carried the
name. A source table the database lacks is a catch-log line. Rebuilt at
each load of this lane: load it after the label lanes.

Measured on the real published tables (full build in the sample
database's `scratch_parties_2_full`, labels read through the read-only
login from `querynz_v4`): 1,154 labels, 1,009 joined; rows joined per
table: party returns 138/140, donors 1,133/1,133, declarations 520/520,
members 243/243, candidacies 1,408/1,476 (49 not a party), MP expenses
24,893/26,689, minister expenses 12,717/13,435, interest returns
2,428/2,521, interests 23,932/24,901, party finance 339/350. Against each
lane's own join: 0 rows disagree. Catch log empty; outside check green
(14 by name, 3 before the reach, 0 differing, the four renames one
registration each; 5 live by the notices and off the page, was 6).

Fast tier green for the whole repository (290 s) and the lane (52 s).
Nothing live written.

## Result (integrator, 2026-10-20 16:27 NZDT)

Merged to main at 801cb0a, gate green: 77 registrations, 149 names, 137
notices read, the labels view resolving 78 of 89 broadcasting-allocation
labels (11 unresolved, carded for keys). The notice-format profile's version
2 is recorded in the profile ledger (count stays 64). The lesson's rule was
cut to the limit. The `pub.party_labels` view goes on the board in the next
commit. The eleven unresolved labels are with `fix-keys-1`. The label lanes
load before this lane in the gate's order.
