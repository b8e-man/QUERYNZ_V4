# procurement-shareholders-donors: known limits and the checkpoint

Step 6.2, template 2 (use case 9, government procurement integrity), the
shareholders half; `procurement-directors-donors` is the other half and
its `limits.md` carries what both share. The question, in words: who among
a winning supplier's people (here its shareholders of record) also appears
as a donor. Each line is a donor row, the shareholder row the links join
it to, the company whose shares that row holds, the supplier on a GETS
award notice joined to that company, and the notice.

## For the register scan only, never for the public site

As for the directors half: a coincidence of record, listed as one, on the
scan's page and files only (plan step 6.2 row 2; step 6.4 is Arthur's open
question). A nominee or trustee holder is flagged on the line and never
shown as an owner.

## Known limits

The template's `limits` are the full list; the directors half's page
explains each. Particular to this half:

- The shareholders register in `pub` is the latest files only (the rows
  read "in the files from companies-2026-07 to companies-2026-08"): a
  holding that ended before July 2026 is not reached.
- A shareholder row carries no number of its holder (`holder_nzbn` is
  empty on all 1,581,955 rows), so a company holding shares is reached by
  the links' name rules like a person.
- Every line is near: the supplier is joined to the company by name alone.

## Checkpoint (21 October 2026, node2)

Real published tables, state in
`querynz_v4_sample/scratch_scan_templates_1`, the shape's additions applied
on a merged copy. Run 20: **6 lines in 47.4 s** (party returns 1 line in
7.2 s, disclosures none found in 20.4 s, candidate returns 5 in 19.8 s);
all 6 near; 0 with a hub; 26 citations; 0 problems. The independent
recount gives 6; the check's read-back holds on each line; a planted
person is caught. `python -m products.scan check` green.

## The six lines, read by eye (run 20; people as initials)

| n | donor (register, year, party, amount) | shareholder, link | company | award (agency · RFx, date, value) | seen |
| --- | --- | --- | --- | --- | --- |
| 1 | party return 2025, National, 66,475.01 | J. J. B. B., full-name (confirmed), 2,667 shares | Online Education | Education · 17759636, Oct 2016, not stated | full names agree; the award is nine years before the gift; dates side by side |
| 2 | candidate return 2023, Labour, 2,100 | M. W., name-only, 1 share | Rotorua Area Primary Health Services | ACC · 32534189, Jan 2026, 0 | a common name: near |
| 3 | candidate return 2023, Green, 20,000 | E. K., name-only, 293,501 shares | Envirostrat | NZTE · 21847888, Dec 2019, 0 | near |
| 4 | the same donor row | E. K., name-only, 33,602 shares | Toha Foundry | Te Puni Kōkiri · 23646415, Sep 2021, 1,500,000 | a second holding of the same name, its own line |
| 5 | candidate return 2023, NZ Loyal, 1,320 | S. Y. W., name-only, 58,708 shares | Rodney Surgical Centre | HealthSource NZ · 25640258, Sep 2022, 5,000,000 | the same donor row met S. A. W. as a director: two different middle names, so at least one is not the donor; near is right |
| 6 | the same | the same | the same | HealthSource NZ · 25680573, Feb 2022, 5,000,000 | each award its own line |
