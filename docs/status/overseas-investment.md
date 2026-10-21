# overseas-investment: where the overseas investment decisions lane stands

Session oio-1 (Opus), 21 October 2026, node2. Merge request `oio-1`. Step 5.3, use case 12.

## The four questions (position in `registers/overseas_investment/position/`, to move)

| Open? | Lawful copy? | Terms | Statute, privacy | Outcome |
| --- | --- | --- | --- | --- |
| yes: no login or challenge; robots states no delay | Crown copyright, CC BY 4.0: copy and adapt, with attribution | the licence and a disclaimer; nothing bars machine reading or reuse | names persons (buyers, vendors, trustees, owners with country and share); gives the street address of the land, often a home; the office withholds some names and figures under the Official Information Act | **captured** |

Nothing is held on terms.

## Done

- `registers/overseas_investment`: capture (each year's listing from 2017, 60 rows a page, resumable, 5 s apart,
  off-peak, stops on a block), three profiles (listing, decision summary, standing-consent notification), the
  reading (no model), load, `pub.overseas_investment_decisions` and `pub.overseas_investment_parties`, check, sample
  (16 summaries, 23 listed rows), 34 tests, 17 of them mutants, fast tier green (29.9 s).
- Proof through the gate, daytime, 58 requests: every year's listing walked (27 pages), 24 summaries. The office's
  listing from 2017: **1,337 rows on 1,318 summary pages** (2017 100, 2018 98, 2019 146, 2020 118, 2021 150, 2022
  181, 2023 149, 2024 149, 2025 136, 2026 110); every year's walk matched its pager. Check run on the proof: red as
  it should be, 31 of 1,337 read; reading and views clean.
- Hard limit 15: street addresses and legal descriptions in the land statement are withheld from the views (by the
  house-number shape, since "14 … Creek" has no street word) and held only in `overseas_investment_private`. The
  agent's contact block is never read; of the Background only its list items and its sentences naming a test.
- Hard limit 16: three summaries in the proof withhold an applicant (and one a vendor) under the Official
  Information Act; the row stays, the name and its ownership origins go.

## Half-done

- No full capture: about 1,320 summaries at 5 s apart is the proposed job's first night (`spec.md` jobs line).
  The check is red until then, correctly.
- Not compared with the old estate's held copy (its reading is not reused).
- Known limits: several persons bolded as one name stay one party row as published; an ownership line keeps
  holder and country together as stated; attachments (decision report PDFs) are counted, not captured.

## Waits on Arthur

- Queue item, default applied: the land's street address is withheld for everyone, companies included (default:
  withheld; a setting to show it where every party is an organisation is the alternative).
- Queue item, default applied: how long a row naming an individual is shown (default: while the office shows it).
