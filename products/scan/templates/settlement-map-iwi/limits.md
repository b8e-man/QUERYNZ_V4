# settlement-map: known limits and the checkpoint (template 3)

Step 6.2, template 3 (use case 14, the post-settlement governance map), on
the iwi and hapū directory (`registers/iwi_directory`, merged as
settlements-1). The question, in words: for each iwi organisation or
post-settlement governance entity in the directory, which iwi and
settlement does it stand for, which charity and which company is it, and
who holds its offices? A line follows one chain of rows, so the question
is six scans, read together by the body's directory key (`tkm/org/…`):

| Scan | A line is | This page |
| --- | --- | --- |
| `settlement-map-iwi` | body · its "organisation of iwi" listing · the iwi | here, with the ten bodies read by eye |
| `settlement-map-settlements` | body · the settlement its entry names | `../settlement-map-settlements/limits.md` |
| `settlement-map-charities` | body · charity of the same name · each officer | `../settlement-map-charities/limits.md` |
| `settlement-map-companies` | body · companies-register entity of the same name · each director | `../settlement-map-companies/limits.md` |
| `settlement-map-societies` | body · society of the same name · each officer | `../settlement-map-societies/limits.md` |
| `settlement-map-shareholdings` | body · holding filed under its name · the company | `../settlement-map-shareholdings/limits.md` |

## For the register scan only, never for the public site

Office holders are register rows about named people. Nothing here goes on
the public site without Arthur's word (6.2 row 3, 6.4, hard limit 14); the
lists live on the scan's page (port 8450, local network) and its files.

## Known limits, all six

The template's `limits` are the full list. In short:

- **No number joins today.** The directory prints a charity number or NZBN
  for 0 of the 185 bodies, so every charity, company, society and holding
  is joined by the folded name alone: near, the reason on the line.
- **The fold sets macrons aside**, as the lanes and the links do: names
  that differ only by a macron meet (Ngāti Hauā, Ngāti Hāua).
- **A blank is a blank.** A body with nothing of its name is listed with
  "none found in", graded confirmed (only register keys joined it). A body
  registered under another name (a corporate trustee, a statutory name)
  meets nothing.
- **The directory's key merges two bodies once.** `tkm/org/ngati-haua-iwi-trust`
  is Ngāti Hāua Iwi Trust (Upper Whanganui, a mandate) and Ngāti Hauā Iwi
  Trust (Waikato, the 2014 Act): the lane's slug drops the macrons that tell
  them apart, so the one row carries both iwi and both settlements, each
  cited to its own page (card `the-iwi-directory-key-folds-two-bodies-into-one`).
  Eight other bodies listed under several iwi print one name on every page.
- **Not held:** the settlement commitments (Te Haeata, behind a login), the
  Māori Land Court (needs a registration) and the Waitangi Tribunal reports
  (Arthur's question). No contact detail, address or marae location is read.

## Checkpoint (23 October 2026, node2)

Real published tables, state in `querynz_v4_sample/scratch_scan_templates_2`,
the shape's additions applied on a merged copy
(`_shape/scan-templates-2-shape.diff`). Directory as loaded 2026-10-23 09:26.

| Scan | Run | Lines | Seconds | Near | Confirmed | Citations | Hubs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| iwi | 7 | 231 | 0.0 | 0 | 231 | 526 | 1 |
| settlements | 8 | 193 | 0.0 | 0 | 193 | 295 | 1 |
| charities | 9 | 2,163 | 0.5 | 2,036 | 127 | 2,286 | 1 |
| societies | 10 | 329 | 0.4 | 163 | 166 | 364 | 1 |
| shareholdings | 11 | 331 | 6.4 | 200 | 131 | 559 | 8 |
| companies | 12 | 198 | 9.5 | 76 | 122 | 265 | 1 |

0 contested, 0 problems on every run. An independent recount (its own fold
in Python over the views streamed whole) gives the same lines and grades
for all six. The check's read-back (`chain_readback`) holds on every scan:
all 185 bodies listed, each join true today, each blank empty today.
`python -m products.scan check` green over all eleven scans, 23.3 s; the
five earlier scans' lines and citations unchanged.

This scan: 178 bodies listed under 224 iwi listings; 7 organisations under
none (Te Ohu Kaimoana and other national bodies). The hub on one line is the
shape's trustee flag on "Te Ohu Kaimoana Trustee Limited", a body's name.

## Ten bodies read by eye (runs 7 to 12; organisations only)

Each body's stored directory page was opened by its hash: the name, the
settlement's text and the iwi listing are on it.

| Body | Iwi | Settlement (stage) | Charity | Companies register | Society | Holdings | Seen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Te Rūnanga o Ngāi Tahu | Ngāi Tahu | 1998 Act | none found | 3 namesakes: two LTD, one public body | none found | 6 | the statutory body meets no charity of its name: a blank, right |
| Ngāti Hāua Iwi Trust | Ngāti Hauā; Ngāti Hāua (Upper Whanganui) | mandate; Ngāti Hauā 2014 Act | CC29892 (26 officers) | charitable trust board | none found | 1 | two bodies under one key: carded |
| Te Rūnanga o Toa Rangatira Inc | Ngāti Toa Rangatira | 2014 Act | CC42382 (56) | incorporated society | 417771 (13) | 31 | right |
| Te Arawa Lakes Trust | 12 Te Arawa iwi | 2006 Act | CC43131 (37) | charitable trust board | none found | 5 | right |
| Rangitāne o Wairarapa | Rangitāne | none named | CC20422, removed (43) | incorporated society, removed | 450918, removed, no officer held | none | right |
| Te Aitanga ā Māhaki Trust | Te Aitanga ā Māhaki | none named | CC39534 (31) | charitable trust board | none found | 8 | right |
| Ngāti Kahungunu ki Wairarapa | Ngāti Kahungunu | none named | none found | a removed LTD of the name | none found | none | a namesake, near: right |
| Te Mana o Ngāti Rangitihi Trust | Ngāti Rangitihi | 2022 Act; CNI collective | none found | none found | none found | none | the collective now cites this body's page |
| Te Korowai o Wainuiārua | Te Korowai o Wainuiārua | mandate, its text "Deed of Settlement signed … 29 July 2023" | none found | none found | none found | none | the directory's flag and its text differ: both shown |
| Aorangi Māori Trust Board | Ngāti Kahungunu | none named | none found | none found | none found | none | a blank, right |
