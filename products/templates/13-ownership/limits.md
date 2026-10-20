# Beneficial ownership and AML checks, domestic half: known limits

Template `ownership` 0.1, use case 13. What the report cannot see, stated
to the reader. Checked on 2026-10-21 against twelve real subjects on
`querynz_v4` (the checkpoint, below). Each line is a limit accepted for now;
the card that would lift it is named.

## What it cannot see

- **Anyone above the first hop.** A shareholder that is a company is filed
  with no business number (empty on all 1,581,955 holder rows; 204,156 of
  them are company holders), so nothing joins it to its own row and its
  holders and directors are not reached. The report names each company
  holder with its shares and files and stops: `holding-chain` fires on
  it, and `ultimate-holders` is **blocked, never clear**. The depth limit
  is four hops (`CHAIN_DEPTH`); the registers reach one (`CHAIN_REACHED`).
  (`a-company-holder-carries-no-business-number`,
  `the-walk-does-not-follow-a-company-holder-up-the-chain`)
- **For whom shares are held.** The register names holders of record. A
  nominee, trustee or custodian is shown as a holder of record and flagged
  by its name (`custodial-holders`); the people it holds for are in no
  register held, and New Zealand keeps no register of trusts, nor of the
  people shares are held for. A holder can hold for others without saying
  so in its name.
- **Sanctions.** No sanctions list is held (Foreign Affairs' Russia
  Sanctions Act register, the United Nations consolidated list, the Police
  designations). `sanctions-lists` is **blocked, never clear**, and counts
  the names a screen would read. The lists are to be acquired (plan 5.3).
- **Limited partnerships and overseas companies.** Neither register is
  held. A holder named as a limited partnership, or with an overseas
  company form (Pty Ltd, Pte Ltd, LLC, B.V., AG …), is flagged by its name;
  one named otherwise is not known as one, so both checks block when
  nothing is seen. "Corporation" and "Inc" are not read as overseas: New
  Zealand statutory bodies (ACCIDENT COMPENSATION CORPORATION) and
  incorporated societies use them.
- **A holder's fraction of the company.** The shares on a row are the
  shares filed for that holding. There is no parcel identifier and no
  issued-share total, and a parcel held jointly repeats its count on each
  holder's row, so no fraction is computed and the 25% line cannot be
  drawn. (`the-shareholders-view-carries-no-parcel-or-issued-shares`)
- **When a holding began.** Holdings are dated only by the monthly files
  they were seen in, from July 2026; every holder line reads "undated; in
  the files from …". A holder that left the file stays listed with its
  last file.
- **A holder of a thousand companies, by count.** The walk flags a holder
  only by its name (nominee, trustee, custodian, the Crown) or as a
  professional director; `holder-hubs` blocks otherwise. Measured
  2026-10-21: no holder holds a thousand companies; the largest,
  NEW ZEALAND TRUSTEE SERVICES LIMITED, holds 659; WYNDHAM SECURITIES
  LIMITED (630) is not flagged by its name.
  (`a-holders-count-of-companies-is-not-read-for-a-hub-flag`)
- **The people on a company, from the company.** Started from a company,
  the report lists its directors and holders and does not follow them:
  their prohibitions, seats, candidacies and donations are not read, and
  `prohibition` and `public-office` block. Start a report from each person
  listed. (`a-company-start-does-not-follow-its-officers`)
- **A member's declared interest in the company.** No link joins a member's
  declaration to a company row yet, so `public-office` cannot fire from a
  company start. (`the-interests-tree-waits-on-the-links-anchoring-interests-to-companies`)
- **A politician on the register is a namesake.** Every link between the
  House and a director row is near by name (598 today), as the design
  requires; `public-office` fires info on them, never amber.
- **A company's donations are near.** The Electoral Commission files a
  donor's name, never a number, so a donation under a company's exact name
  is listed with the namesakes, near (RANK GROUP LIMITED: 13 rows).
  `political-money` fires on them at info.
- **A bankruptcy.** No link rule joins a Gazette bankruptcy notice to a
  person; the check is always blocked. A blank there is not a clear.
- **Past roles.** The companies file lists current roles only, so a
  person's checks over their companies fire or block, never clear
  (`HISTORY = False`, as in templates 3 and 2).
- **A busy person.** The walk lists 40 companies and reads 12; past those,
  every check that needs them blocks (subject 11: 111 companies past the
  limit, 177 links unread).
- **The securities register, the Insolvency Register, court judgments,
  financial service providers, charities and land titles** are not held.
- **Overseas registers and trusts** are named in the not-held section's
  text, not in the shape's not-held list.
  (`the-catalogue-names-no-overseas-registers-or-trusts-as-not-held`)
- A company's registered office is shown and flagged when 50 or more
  companies share it. No residential address is held in any view read.

## The checkpoint, 2026-10-21

Twelve subjects through `python -m products.report render REF --template
ownership` (keys in `checkpoint.list`), each read against `pub.shareholders`
and `pub.companies`. All twelve built, none refused by the presentation
rules, each in under 7 seconds. No address-shaped line outside a
registered office; no word of cause or ownership in the template's text.

| # | Subject | What it tests | Read against the tables |
| --- | --- | --- | --- |
| 1 | SAILPLANE SERVICES 2005 LIMITED | A trustee company holding jointly with two people | 5 holders; the trustee flagged and stopped at; parcels of 200 and 300 shown, not summed |
| 2 | FOLEY WINES LIMITED | Ten company holders, three nominees | 10 of 10 companies, matches; ACC was flagged overseas: **fixed** |
| 3 | CANDLE SUPPLY LIMITED | An Australian nominee holder | Nominee and overseas both fire on Kilara Nominees Pty Limited |
| 4 | SEASONAL SOLUTIONS CO-OPERATIVE LIMITED | A co-operative with limited partnership holders | 37 of 43 companies, matches; three partnerships flagged |
| 5 | STREAMLINERS NZ LIMITED | A general partner holding for a partnership; a trust | Both flagged; 2 of 2 companies |
| 6 | SACRED HILL VINEYARDS LIMITED | In receivership and liquidation | Status red; three Gazette notices, each with its own date |
| 7 | BSC INDIAN SWEETS &TAKEWAY LIMITED | Removed, no holders | The chain blocks ("an empty list is not a finding") |
| 8 | RANK GROUP LIMITED | A political donor company | 13 donation rows near; the near-money clear **fixed** to fire |
| 9 | A director with a confirmed prohibition | A person start | Prohibition red, its term and "ended before" stated |
| 10 | A director whose name matches a 2026 candidate | Domestic public office | public-office info, a namesake until confirmed |
| 11 | An individual holding 283 companies | A busy, contested group | custodial and money clears on a short walk: **fixed** to block |
| 12 | A party-return donation row | A filed-row start | Every check blocks; nothing clears |

Fixed at the checkpoint (each with a property and a mutant in the tests):
the overseas pattern read "Corporation" and "Inc"; a near donation let
`political-money` clear; a short walk let `custodial-holders` and
`political-money` clear; share counts arriving as decimals printed "no
share count filed".

The checkpoint ran on `pub.links` of 2,614,679 links, after the links
reload of 07:50 failed with node2's network (see
`node2-lost-its-wired-link-and-an-orphaned-links-load-holds-its-locks`);
re-run it once the integrator has reloaded the links.
