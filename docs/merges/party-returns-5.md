# party-returns-5: Part A on 52 returns; three declarations mended; a shifted pairing and an address fragment fixed
branch: session/party-returns-5 (pushed; f6da93b)
session: party-returns-5 (session 5)
raised: 2026-10-20
claims: registers/party_returns/ (`read.py`, `schedule.py`, `donors.py`, `replay.py`, `tables.sql` comment, `sample.list` +3, tests); cards: 2 comparison cards closed, 2 measured, 3 lane cards updated, 2 opened; decision `may-part-a-pass-a-rounding-cent`; lesson `the-sum-cannot-see-a-shifted-line-in-the-text-layer-either`; docs/status/party-returns.md

Step 4.1, the brief's fifth tranche. Every change measured on all 152
landed returns, replay only, no model called; every published (name,
amount) then set beside the old estate's rows of the same document hash
(811 rows on 42 returns both read: 4 differ, all spellings or one
figure per donor against the old per-date split).

**Result: Part A published on 52 returns (1,133 rows; was 38, 843), nil
63, set aside 25 (was 37). Declarations 140 (was 137).**

- **Part A over the stored page readings.** Where Part A fails on the text
  layer and the page reader has stored readings (the lane's stamp) of the
  text pages, Part A is read again over them, taken only if it reconciles:
  Labour 2020, Labour 2024, Green 2019. A set-aside line otherwise names
  the part's text pages with no stored reading.
- **Shapes:** a numbered name with its row on the unnumbered lines below
  (National 2018, DemocracyNZ 2022 both, NZ First 2024 amended, TOP 2023);
  a donor's `Aggregated total` line dropped where it equals its rows (NZ
  First 2019, across a page); bare row numbers in a stacked page (NewZeal
  2023); a whole figure after `NO` (NewZeal 2024); one figure on a page
  (TOP 2024); a `see attachment` page names no donor (National 2025, 148
  rows, $2,727,334.14); a donor's dated rows over a page-reader page break
  (ACT 2017).
- **Two faults in rows already published, fixed.** ACT 2022 page 2: a $50
  gift carried the next donor's name, whose $100,000 was published as
  from "Auckland"; the sum held (lesson filed). Labour 2019 and 2020 (both
  copies): one donor's name carried a retirement village, a home-address
  fragment (hard limit 15). Fixed by taking a text cell's name from its
  first line and ending a name at postnominal letters. Name cut also stops
  at a care-of company or accountant, `Parliament`, a spaced dash; keeps
  `22 E.A.W Limited`. NZ First 2024's MPs lose `Parliament Buildings`.
- **Declarations mended from the part pages** (`read.recover`, pixel
  route only, every part page agreeing to the cent): NZ First 2019
  `parts-confirmed` $369,535.17 (the frozen site's $368,535.17 is a
  misread digit; card opened), TEA Party 2020 $154,619.77, Vision NZ 2022
  `part-pages` $20,776.49. All three equal the Commission's table. New
  `total_check` values; `tables.sql` comment only, no column change.
- `python -m registers.party_returns.replay rereads RUN.json`: every
  set-aside return with its hash and the pages to queue. Today: 17 pages
  for a cell-scale re-read; Labour 2023 pp 4, 5, 7 and Green 2020 p 4 have
  no stored reading; National 2024 p 3 (the reader looped). The full list
  is `/home/user/querynzv4-work/scratch/party-returns-5/rereads.tsv`.

Cards: `party-years-the-frozen-site-totals-…` closed (NZ First 2019 and
Vision 2022 held; Te Pāti Māori 2021 is `keys`' label card; NZ Loyal
2023 is held and the rebuilt home page lists the party twice, which is
the site's; the frozen site holds no Alliance return). `the-rebuilt-lane-
holds-declared-totals-…` closed as accepted. `part-a-rows-are-read-on-a-
minority-…` and `part-a-rows-the-frozen-site-has-…` stay open with their
figures and what each remainder needs.

For the comparison's next run, after this loads: `part-a-rows-not-read`
(1,909) and `return-with-no-reading` (32) should fall; NZ First 2019's
total moves under its new card; `rows-only-the-frozen-side-has` loses
ACT 2022's pair.

For the load: no schema change. `sample.list` gains Heartland 2022,
Vision NZ 2022 and ACT 2017 (landed already).

Fast tier: `registers/party_returns` green (102.7 s, sample filled into
`scratch_party_returns_5`). Whole repository: red in 291.8 s on one test only, `tests/test_generators.py`: `docs/board.md` is stale because this branch adds two cards. The board is generated, so it is yours to rebuild at the merge; the fence won't let me restore it, so it sits modified and uncommitted in the working copy.

Hard limit 11: while tracing the Labour address fragment this session
printed that fragment (a retirement village's name) into its transcript
several times, and one party secretary's name, read off a declaration
image. Nowhere else: not in a card, commit or file.

## Result (integrator, 2026-10-20 14:59 NZDT)

Merged into main as 7938e81 (merged main first). Done at the merge:
records regenerated (the lesson, the queue item, the cards); status and
briefs. Fast tier and gate green; the gate's load: 152 documents, 140
rows, 12 set aside, 1,133 donor rows, 10 loan rows, 14 returns replaced
by an amendment; published. Nothing queued for the page reader: ruling
62 (Arthur, 14:30) holds document reading until the build is done, so
the `replay rereads` list is the queue for later. The comparison's next
run (08:45) should show the two causes fall. Arthur's to rule: the
rounding cent (National 2023, queue, default no) and NZ First 2019's
total on the frozen site (an emergency fix only on his word). The
hard-limit 11 note is recorded here and nowhere else. The session ran
headless from the integrator as Opus, about 70 minutes.
