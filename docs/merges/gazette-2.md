# gazette-2: director prohibitions and liquidator appointments read
branch: session/gazette (pushed; 2f4415b, 38e694c)
session: gazette (session 2)
raised: 2026-10-20
claims: registers/gazette/ (new `prohibitions.py`, `liquidations.py`; read, load, check, tables, publish, sample.list, spec, pane, tests; `profile-proposed.jsonl` now holds two new profiles); cards `the-gazette-lane-leaves-the-other-insolvency-bankruptcy-and-appointment-notices-unread`, `liquidator-appointments-are-checked-only-against-the-gazette-s-own-section-code`, and `the-gazette-lane-reads-only-the-celebrant-lists-so-far` closed; lesson `a-masked-gazette-sample-still-leaks-through-its-lowercase-words`; docs/status/gazette.md

Step 4.1, the status file's next two items, each its own profile and tranche.
Every figure below is measured on all 207,133 notices of the pinned export,
not the sample. Every look at notice text was masked.

**Director prohibitions** (profile `gazette-director-prohibition` v1). One
`To: <name> Of: <address>` template since 2001, mostly section `ot`.
Recognised by the Companies Act or the FMC Act together with the management
words ("hereby prohibit" alone also catches a drug-prescribing order and a
vaccine notice; both excluded). 537 notices, all read; 538 people; every
field (statute, term or "permanent", start, Dated) read on all 537. Six
actions from the operative words: prohibition 523, court order 7, banning
order 4, substitution 1, variation 1, revocation 1. The `Of:` address goes
to `gazette_private.prohibition_addresses` only (538). Notices that revoke,
replace or vary another name it by number. The named notice's rows carry
`superseded_by`/`superseded_how`. `pub.gazette_prohibitions` withholds the
name where the notice was revoked, because one was revoked "as published in
error" for naming the wrong person. A revocation's own text is never read
for a name.

**Liquidator appointments** (profile `gazette-liquidator-appointment` v1).
Recognised by the Gazette's own section code `al`. 43,587 notices: 43,478
read (700 with a part set aside), 109 set aside. 60,711 company rows
(15,646 from 2019) and 45,067 liquidator rows. Two shapes: notices, and the
Official Assignee's lists, in both the `NAME | date` form and the older
"date, then names" form. A title is cut only where every part ends in a
legal suffix, so `SMITH AND JONES LIMITED` stays one company (the old
reader split it). Who appointed comes from s 241(2)(a/b/c) or the words.
Dates come per company where the notice prints them "below". Liquidators
come from the signature (39,572; 29,227 named in full in the body, 15,671
by surname only as when initials sign, 169 not at all), else from the
operative sentence. No address, telephone or email is read: a director
acting as liquidator may print a home one.

Outside check (`check.py`, exit 0 on the full load): the celebrant series
as before. For prohibitions, the 531 notices the Gazette titles "Notice
Prohibiting Person" are all read, and the 3 notices named by number by a
later notice are held, read and marked. For liquidations, every notice
filed under `al` is taken by the profile. That proves coverage only. The
real figure is the companies register, which is carded until that lane
merges. The full lane loads in 32.1 s (was 12.4 s).

Fast tier: the lane's 42 tests green on the sample (51 notices now; hard
cases named in `sample.list`). Whole repository: one failure,
`tests/test_generators.py`, because my cards and lesson make
`docs/board.md` and `lessons/INDEX.md` stale (generated; yours to
rebuild). The test rewrote `docs/board.md` in my working copy; it is left
uncommitted.

For the merge, please:
- Append the two lines of `registers/gazette/profile-proposed.jsonl`
  (`gazette-director-prohibition` v1, `gazette-liquidator-appointment` v1)
  to `support/profiles/profiles.jsonl` and delete the proposed file.
- New private table `gazette_private.prohibition_addresses`: the session
  reader must not be granted it (as with `celebrant_addresses`).
- `gazette.notices` gains a column `supersedes`; `pub.gazette_notices`
  carries it. The load drops and recreates the views, so nothing to migrate.
- Two scratch schemas in `querynz_v4_sample` were refilled by my full load
  and still need dropping: `scratch_gazette_full` and
  `scratch_gazette_full_private` (the second holds the celebrant and
  prohibition addresses).

## Result (integrator, 2026-10-20 07:25 NZDT)

Merged into main as c5c30dc (merged main first). Done at the merge: the
two profiles appended with `add_version`, the proposed file removed, the
shipped-profiles test at 49; the lesson's rule cut from 263 to 232
characters; board and lessons index regenerated. Fast tier and gate
green; the gate's load: 207,133 notices, 537 prohibition notices read
(538 people, addresses private, names withheld where revoked), 43,478 of
43,587 liquidation notices read (60,711 company rows, 45,067 liquidator
rows); published in 33 s. `gazette_private` is readable by the owner
only, checked after the publish. The two scratch schemas in the sample
database (`scratch_gazette_full`, `_private`) stay Arthur's psql. The
session ran headless from the integrator, about 70 minutes.
