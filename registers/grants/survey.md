# Where grants are published: the survey of 21 October 2026 (grants-1)

Through the fetch gate, daytime, serial, 5 s apart (the catalogue's 10 s honoured): 105 page requests and one
robots file per host. Each society: its home page, then at most three of its own pages whose link says grants.

## The Department of Internal Affairs (read)

| What | Where | Shape | Window | Licence |
| --- | --- | --- | --- | --- |
| National file of class 4 grants, "Grants from Gaming Machine Profits" | catalogue.data.govt.nz, package `class-4-grants-data` | one CSV, 178,739 records, 19 columns: society, recipient as reported, final name, NZBN, charity number, status (Accepted 116,684, Declined 62,047, Refunded 8), amounts requested and granted, decision date, year, two categories, refund, territorial authority, region. No purpose | decisions 2021 to 2025; updated yearly | CC BY 4.0 |
| Lottery committees' records of grants | www.communitymatters.govt.nz, one page per committee and round | an h1 and one table, Name and Amount, an asterisk for a multi-year grant. No purpose, no date, no number | the financial year in the heading | Crown copyright; the Department's CC BY 4.0 (its own page not read) |
| The list of operating societies | granted.govt.nz (script bundle) | 31 societies, 770 venues, each society's website | 21 October 2026 | the Department's |

The Lottery records hang off no index page. The site's "ask us" answer that lists them refused (HTTP 403), so
the capture walks the site whole. The old Lottery recipient CSVs on the catalogue (to 2017/18) were not
reached: the catalogue then served a challenge.

## The 31 societies (surveyed, not read)

| Class | Societies | What the survey saw |
| --- | --- | --- |
| A. Grants lists as files | NZ Community Trust (one PDF, 2023/24 to July 2026); Air Rescue Services (approved and declined, quarterly, 2017 to 2025, about 40 PDFs, typed: exported from Excel); Pelorus Trust (approved and declined pages, 24 PDFs, 2025 to 2026); Aotearoa Gaming Trust (funding distributions, 3 PDFs); One Foundation (9 PDFs, 2020 seen); Trust Aoraki (a table of monthly PDFs, 2013 to 2026, 37); New Horizon (approved grants, 2 PDFs); Milestone Foundation (41 PDFs, 2020 to 2024); We Care (historical grants, 22 PDFs, 2021 to 2026) | Each society its own layout: one profile per layout, read from the text layer |
| B. Grants pages reached, no list among the first three | Pub Charity, Lion Foundation, Mainland, Bluesky, ILT (one spreadsheet, a form), Dragon, Grassroots Central, Rano, Kiwi Gaming, First Light (its menu names "Applications approved" and "declined", not reached), Oxford Sports Trust, Akarana | The whole-site walk from the grants page will find the list or show there is none |
| C. No grants link on the home page | Grassroots Trust, North and South Trust, The Trusts Community Foundation, Trust House, Redwood, Constellation | Likely built by script or a portal; a walk, then a headed browser shown no challenge |
| D. The listed address is dead | Four Winds Foundation and Manukau Counties Community Facilities (both `fourwindsfoundation.co.nz/MCCFCT`, 404) | The Department's list carries a broken address |
| E. Grants on another host | Trillian (`trillian.co.nz`, now named in the position), Youthtown (`youthtowntrust.org.nz`, not named) | The gate refused, correctly |

Every society's 2021 to 2025 grants are already in the Department's file. The societies' own lists add 2017 to
2020 (ruling 71's window) and the purpose as printed.
