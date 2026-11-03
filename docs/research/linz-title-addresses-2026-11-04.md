# Each title's street address, from the LINZ property spine (4 November 2026)

Arthur, 3 November 2026: "why no address on land ownership?" and "gather everything". Counts only; no address, title
number or name is written here. The addresses are held in `linz_private.title_addresses`, never published (hard limit 15
binds a product's surface, ruling 102); no `pub.linz_*` view carries an address column, and the lane's check is red on
one.

## The source

The LINZ Data Service publishes an aspatial join, so no geometry and no PostGIS are needed. All three are CC BY 4.0, as
each catalogue entry states, and are updated weekly:

| Source | Rows (stated, 3 November) | What it gives |
| --- | --- | --- |
| table 113970, NZ Properties: Property-Title Reference | 2,470,714 | a title number on a unit of property (a rating unit) |
| table 115638, NZ Properties: Property-Address Reference | 6,708,160 | an address id on a unit of property |
| layer 123113, NZ Addresses (AIMS), attributes only | 2,434,677 | the address as LINZ gives it (`full_address`) |

The join: title → unit of property → address id → address (`registers/linz/load.py`, `JOINED_BY`). The other candidates
(the address points inside the title polygons of layer 50804, or inside the parcels of layer 50772) need a geometry
and a point-in-polygon pass; they are not needed for the 92% the spine covers, and stay the way to reach the rest.

## The first full build (scratch, the pulls of 3 November 23:42 to 4 November 00:16)

Pulled through the fetch gate, one request at a time, off-peak: 248 + 244 + 671 pages, 1,163 requests, about 33
minutes. Read in 590 s with the other three sources (a 10-minute load in all); 108 property-title rows and 851
property-address rows set aside for a missing join key; the check reconciles.

| Measure | Count |
| --- | --- |
| titles (layer 50804) | 2,457,581 |
| titles on the spine at all | 2,408,944 |
| **titles with a street address** | **2,270,831 (92.4%)** |
| rows in `title_addresses` (title and address) | 7,202,059 |
| distinct addresses joined | 2,380,515 |
| titles with one address / 2–5 / 6–50 / over 50 | 1,846,932 / 339,757 / 62,284 / 23,498 |
| units of property with one title / 2–5 / 6–50 / over 50 | 2,037,652 / 75,788 / 6,882 / 116 |
| addresses current / proposed | 7,192,745 / 9,314 rows |
| owners whose title has an address (of them individual) | 4,725,258 of 5,745,217 (4,004,931 of 4,920,640) |

By title type (titles, with an address): Freehold 1,988,868 / 1,849,371; Cross lease 210,966 / 206,125; Unit Title
182,715 / 175,505; Leasehold 30,538 / 26,481; Supplementary Record Sheet 15,962 / 2,183; Timeshare 13,412 / 5,819; Records
Embodied in the Register 9,907 / 3,205; Gazette Notice 4,526 / 1,530; Life Estate 687 / 612.

Without an address: 48,637 titles are not on the spine (the spine is built from rated properties), and 138,113 are on a
unit of property with no address row. A unit of property carrying many addresses (an apartment building's units) or
many titles is said so on each row (`addresses_on_property`, `titles_on_property`): the address is the property's,
not always the title's own.

## The nights

`qv4-linz-capture` takes the three with the others, weekly, small first (`capture.DUE_ORDER`); about 1,160 pages a week
more. `qv4-linz-load` reads them and publishes `linz_private.title_addresses` with the rest, on green only; the floor is
85% of titles with an address (`check.TITLE_ADDRESS_FLOOR`).
