# procurement-directors-donors: known limits and the checkpoint

Step 6.2, template 2 (use case 9, government procurement integrity), the
directors half; `procurement-shareholders-donors` is the other half (a
chain lands on one view per step: card
`a-scan-step-cannot-land-on-one-of-several-views`). The question, in words:
who among a winning supplier's people also appears as a donor. Each line
is a donor row, the director row the links join it to, the company that
row sits on, the supplier on a GETS award notice joined to that company,
and the notice.

## For the register scan only, never for the public site

A donor joined to an award is the plainest case of a coincidence taken
for more than it is (plan step 6.2, row 2). This scan lives on the scan's
page (local network, port 8450) and its files, and nowhere else. Whether
the award join ever appears on Follow the Money is Arthur's open question
(step 6.4); nothing here is built for it. No line says why an award was
made or a donation given; the dates are each register's own, side by side.

## Known limits

The template's `limits` are the full list. In short:

- **Every line is near today.** The supplier is joined to the company by
  name alone: the GETS supplier file publishes no usable business number.
- **The donor to the director is the links' join**, rule by rule:
  `full-name@1` (confirmed) or `name-only@1` (near, the link's reason on
  the line). A common name meets many directors: of the 80 lines, 75 come
  through `name-only@1`.
- **A filed donor row is in no group**, so a line reaches only the
  director rows the links join to the donor row itself, not the person's
  other directorships (measured: 718 direct pairs against about 6,000
  director rows in their groups). The chains setting does not widen it
  (card `a-person-step-cannot-reach-a-filed-row-through-the-groups`).
- **One donation row per line.** A party-return row an amendment replaced
  is listed beside its amendment (113 of 1,315 rows carry `replaced_by`;
  card `a-scan-step-cannot-land-on-one-of-several-views`). A disclosure and the
  return covering the same gift are separate lines, never summed.
- **No address is read**; a suppressed director shows "name suppressed".

## Checkpoint (21 October 2026, node2)

Real published tables, state in
`querynz_v4_sample/scratch_scan_templates_1`, the shape's additions applied
on a merged copy. Run 19: **80 lines in 49.4 s** (party returns 32 lines
in 10.2 s, disclosures 1 in 21.6 s, candidate returns 47 in 17.6 s); all
80 near, 0 confirmed, 0 contested; 6 lines with a hub (a professional
director at 111 directorships; a thousand-company office); 147 citations;
0 problems. 16 donor rows, 10 directors, 10 companies, 55 notices.

An independent recount (Python: the links of the two rules from every
donor row, the director's company, the check's fold against every
supplier name) gives 80; the check's read-back holds on every line (the
link today, the company key, the names folding alike, the supplier on the
notice); a planted person is caught. `python -m products.scan check` green.

## Twelve lines read by eye (run 19; people as initials)

| n | donor (register, year, party, amount) | director, link | company | award (agency · RFx, date, value) | seen |
| --- | --- | --- | --- | --- | --- |
| 1 | party return 2024, ACT, 8,000 | D. I. W., name-only | Walker Property Services | Education · 26328522, Apr 2023, 37,562 | middle name filed on one side only: near, right |
| 5 | party return 2023, ACT, 15,980 | same | same | same | each donation row its own line |
| 13 | party return 2025, National, 11,470 | M. D. G., full-name (confirmed) | Mike Greer Commercial | Kāinga Ora · 21518501, Jun 2020, 0 | hub: 111 directorships, flagged |
| 21 | party return 2022, ACT, 5,000 | D. I. W. | Walker Property Services | Education · 26328522 | four rows of one return, four lines |
| 33 | disclosure, ACT, 39,530 | D. T. B., full-name (confirmed) | ICBC (New Zealand) | University of Auckland · 24162432, Oct 2021, 0 | full names agree; still near (supplier by name) |
| 34 | candidate return 2023, Green, 2,000 | L. W., name-only | Whanau Tahi | MidCentral DHB · 23866418, Jul 2021, 0 | near, right |
| 35 | candidate return 2023, Green, 7,000 | J. R. S., name-only | Axenic | MBIE · 5759284, Dec 2015, not stated | a common name: near is the right grade |
| 36 | candidate return 2023, Te Pāti Māori, 4,100 | D. J., name-only | a psychological services company | ACC · 29111968, Jan 2024, 0 | a common name; near |
| 37 | candidate return 2020, Labour, 5,000 | P. R. T., name-only | Kakapo Design | Education · 22076344, Dec 2021, 0 | near |
| 39 | candidate return 2023, NZ Loyal, 1,320 | S. A. W., name-only | Pattle Delamore Partners | Christchurch City Council · 21021168, Nov 2019, 0 | the same donor meets a different S. W. as a shareholder: why near |
| 77 | candidate return 2023, Green, 2,000 | D. A. G., name-only | Honeywell | Health NZ · 27561319, Nov 2023, 0 | near |
| 79 | candidate return 2023, Labour, 1,669.50 | R. G. M. K., name-only | Kenderdine Electrical | University of Canterbury · 31988521, Sep 2025, 417,326 | hub: thousand-company office, flagged |
