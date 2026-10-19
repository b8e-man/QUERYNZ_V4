# parties-1: the Register of Political Parties and each party's lifecycle
branch: session/parties (pushed; 2be6f5c)
session: parties (session 1)
raised: 2026-10-19
claims: registers/parties/ (new `notices.py`, `register.py`, `lifecycle.py`, `load.py`, `profile-proposed.jsonl`, tests `test_parties_lane.py`; capture, read, check, tables, publish, sample, pane, spec); cards `keys-parties-should-read-the-party-names-the-lane-publishes`, `six-parties-are-off-the-register-with-no-cancellation-held`; lesson `look-for-the-source-s-own-statement-before-inferring-a-link`; docs/status/parties.md

Step 4.1. The lane reads the Commission's register page (case 1, copied
by hash from `var/staging/ec-party-register/`) and its Gazette notices on
the register, which the old estate holds only as text: exported once on
19 October 2026 to one dated JSON-lines file (case 2, pinned in
`capture.EXPORT_SHA`; every row from it says "taken from the old estate's
tables; original not held"). It fetches nothing.

A registration is the party (old ruling 349); a renamed party is the same
party. The notices state every rename in words, in three shapes; the old
estate inferred its four from registration windows only because its
parser read none of them. Here each stated rename is read, and the window
(the page's registration day against the notice's) is the check that the
page and the notices describe one registration. A party cancelled and
registered again (New Zealand Loyal, United Future) is two registrations.

Measured on the sample (which is the lane's whole input; scratch schema,
nothing live written): 136 notices, 210 resolutions read, 0 set aside;
the 135 that name a party (registered, cancelled, renamed, abbreviation)
all resolved to a registration. 78 registrations: 50 opened by a held
notice (2001 on), 25 first met in a later notice (registered before the
notices begin), 3 from the page alone; 17 on the register, 55 cancelled.
One corrigendum applied (2026-au413 to 2026-au375). Outside check: 14 page parties joined by name, 3 before the
notices' reach (National, Labour, NZ First), 0 differing; the four known
renames (Māori Party, Conservative Party of New Zealand, NZ Outdoors
Party, The Opportunities Party) one registration each. Six parties are
live by the notices and absent from the page with no cancellation held
(card). Labels: 31 of 34 unresolved party-return rows and 46 of 53
unresolved disclosure rows resolve by name and window alone, once
`keys.parties` reads `pub.party_names` (card, blocker; `keys/` is outside
this fence).

For the merge, please:
- Append `registers/parties/profile-proposed.jsonl` (profiles
  `ec-party-register-page` v1 and `gazette-party-register-notices` v1) to
  `support/profiles/profiles.jsonl` with `add_version` and delete the
  proposed file; `read.profile_version()` takes the ledger's first.
- The export's bytes are in the store (`/mnt/hdd2/qv4-docs/dc/dc19fb…`);
  `copy_all` lands them into the database it is given. The register page's
  bytes (0f035f…) are in the store too: the old job overwrites its file
  nightly, so a later load reads that night's page and the sample keeps
  this one.
- `capture.export_notices` queries the OLD database's `gazette` schema
  (`nzbn_canonical`, read-only login). It sets the search path to that
  schema rather than qualifying the table, so
  `tests/test_imports_one_way.py` does not take it for a query into this
  estate's gazette lane. If you would rather the scanner carry an explicit
  exemption for old-database exports, say so and I will qualify the name.
  The export is run once; nothing runs it at load.
- Records: the cards and the lesson make `docs/board.md` and
  `lessons/INDEX.md` stale; `tests/test_generators.py` rewrote
  `docs/board.md` in my working copy, which the fence will not let me
  restore. It is not committed. Please regenerate both at the merge.
- Note: the old read-only login reaches the old PRIMARY (node1 is down,
  node2 primary since 17 October); the export was two small reads.

## Result (integrator, 2026-10-20 04:15)

Merged into main as a2ccef5 (merged main first; board and lessons index
regenerated). Done at the merge: `ec-party-register-page` v1 and
`gazette-party-register-notices` v1 appended to `support/profiles/profiles.jsonl`
with `add_version`, the proposed file removed; the shipped-profiles test
now expects 25. The export's search path stays as written: the comment in
`capture.py` says why, and the scanner guards this estate's schemas, not
the old database's. Fast tier and gate green; the gate's staging load:
17 page parties, 136 notices, 210 events, 135 resolutions all resolved,
78 registrations, 149 names, 2 corrections, 17 on the register, 6 off it
with no cancellation held, 0 set aside; published. The `keys.parties`
card is a fix session on `keys`, briefed in `docs/briefs/next.md`.
