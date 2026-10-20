# gazette-3: the other insolvency, bankruptcy and appointment notices; the printed celebrant tables; the register check
branch: session/gazette (pushed; 68d1b03, cfdff09, c873fd2, 612f531, 3c4d423, fd95997, 2458cce, ae81e73)
session: gazette (session 3)
raised: 2026-10-20
claims: registers/gazette/ (new `register.py`, `entries.py`, `removals.py`, `windingup.py`, `receiverships.py`, `creditors.py`, `bankruptcies.py`, `appointments.py`; read, load, check, tables, publish, notices, liquidations, celebrants, sample.list, spec, tests; `profile-proposed.jsonl` holds nine new profiles and `gazette-celebrant-list` v2); cards `the-gazette-lane-leaves-the-other-insolvency-bankruptcy-and-appointment-notices-unread`, `liquidator-appointments-are-checked-only-against-the-gazette-s-own-section-code`, `twelve-printed-celebrant-tables-are-unread` closed; cards `appointment-notices-whose-appointees-run-together-are-unread`, `annulled-bankrupts-the-reader-cannot-name-stay-published-on-earlier-rows`, `bin-fast-runs-the-system-python-in-a-working-copy-without-a-venv` opened; lessons `join-a-reading-to-the-register-it-names-before-trusting-its-own-counts`, `a-mis-cut-list-of-people-can-publish-a-street-as-a-name`; docs/status/gazette.md

Step 4.1, the status file's next items, seven tranches, each its own
profile, every figure measured on all 207,133 notices of the pinned export
(a full load into a scratch schema: 88 s, 4.5 GB peak), not the sample.
Every look at notice text was masked (vocabulary mask; for notices about
people, case classes only).

**The register check** (`register.py`). Every company row of every
insolvency profile is joined at load to the companies lane's `pub.companies`:
by the printed company number (companies register only), else the one entity
of that name alive on the notice's date. Unmatched, or several alive, is a
catch-log line, never the nearest name. Joined: al 59,787 of 60,911 (98.2%;
4,333 of 4,384 printed numbers agree by name), ds 96.7%, aw 96.0%, md 93.8%,
aa 91.9%, ar 90.9% (a company sold out of receivership is often renamed).
The join found reader faults in gazette-2's liquidations: brackets that are
part of a name were cut out ("FISHERIES (2019) LIMITED"), "TRUSTEES LIMITED"
was cut at TRUST, list rows after a bracket were merged. All fixed (reader
`liquidations 2`).

**Company notices** (one table, `company_notices`, 1,478,439 rows; receivers
and administrators in `practitioners`, 6,025). Profiles:
`gazette-removal-notice` (ds 29,783; 1,439,717 rows, mostly the Registrar's
lists), `gazette-winding-up-application` (aw 30,452; court, CIV reference,
hearing, the plaintiff by name only, never its address for service),
`gazette-receivership` (ar 5,012; a subject with no legal suffix may be a
person's property and is set aside, never published as a company),
`gazette-creditors-notice` (md 1,479: the old family label "administration"
was wrong and is corrected), `gazette-administration` (aa 388).

**Bankruptcies** (`bankruptcies`, 65,299 people; profiles
`gazette-bankruptcy-list`, `gazette-no-asset-procedure-list`,
`gazette-bankruptcy-notice`). Every address and formerly-of address goes to
`gazette_private.bankruptcy_addresses` (65,021). A name field that reads as
an address sets its record aside. A person an annulment names is withheld
from `pub.gazette_bankruptcies` on that row and every earlier row naming
them (552 rows).

**Appointments** (`appointments`, 3,155 appointees from 2,514 of 4,509
notices titled "Appointment…" in go, vr, au, ps, gn; profile
`gazette-public-appointment`). Where an appointee lives is never kept.
Outside check: 125 of 134 "Honourable" appointees (not judges) since 2021
are MPs by surname in `pub.members`.

**Printed celebrant tables**: read last, cut by the 825 organisations the
delimited lists print; 36,315 records; 79.7% of the people are named by a
delimited list too.

`check.py` exits 1 below any floor, on any notice of those sections not
taken by its profile, on an annulled person published by name, or if the
register was never joined. Green on the full scratch load.

For the merge, please:
- Append the ten lines of `registers/gazette/profile-proposed.jsonl` to
  `support/profiles/profiles.jsonl` with `add_version` (nine new v1, and
  `gazette-celebrant-list` v2) and delete the proposed file.
- New private table `gazette_private.bankruptcy_addresses`: never granted
  to the session reader, like the other two.
- New tables `company_notices`, `practitioners`, `bankruptcies`,
  `appointments`; `liquidations` gains `register_key`, `register_match`;
  views `pub.gazette_company_notices`, `pub.gazette_practitioners`,
  `pub.gazette_bankruptcies`, `pub.gazette_appointments`. The load drops and
  recreates, nothing to migrate.
- The load reads `pub.companies` (the register join) and the check reads
  `pub.members`; the gate's load needs both published first.
- `docs/board.md` and `lessons/INDEX.md` are stale (generated; yours to
  rebuild); the root fast tier fails only on that.
- Two scratch schemas in `querynz_v4_sample`, `scratch_gazette_full` and
  `scratch_gazette_full_private` (the second holds addresses), refilled by
  my full loads; dropping them is Arthur's psql, as before.
- Card `bin-fast-runs-the-system-python-in-a-working-copy-without-a-venv` is
  in `bin/`, yours.

## Result (integrator, 2026-10-20 12:41 NZDT)

Merged into main as 8e348ed (merged main first). Done at the merge: the
ten profile lines appended to the ledger (nine at version 1,
`gazette-celebrant-list` at 2; the ledger at 101 lines); records
regenerated. Fast tier and gate green; the gate's full load, 88 s, then
published: `pub.gazette_company_notices` 1,478,439,
`gazette_practitioners` 6,025, `gazette_bankruptcies` 65,299,
`gazette_appointments` 3,155. `gazette_private.bankruptcy_addresses` is
owner-only like the other two. In the records commit after the gate:
the four views in the board's catalogue, written from the columns since
`pane.md` was not extended (carded for the lane:
`the-gazette-pane-spec-omits-the-four-tables-of-gazette-3`); the two
`bin/fast` cards closed by the fix in `bin/fast`. Arthur's to clear:
`scratch_gazette_full` and `scratch_gazette_full_private` in
`querynz_v4_sample` and the session's scratch folder. The session ran
headless from the integrator as Opus, about two hours.
