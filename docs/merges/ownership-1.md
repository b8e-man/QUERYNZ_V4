# ownership-1: template 13, beneficial ownership and AML checks, domestic half

Branch `session/ownership-1`, on top of main at d003ed3, head 257550a. Scope `products/templates/13-ownership/`, plus this
session's five cards, one lesson and its status file. Edits nothing of `products/report/`.

## What it claims

1. **The template** (`template.toml`): 19 pub views, each with licence, attribution and refresh. Six sections in a
   compliance analyst's order: the entity and its namesakes apart; its holders of record with their shares and files,
   as far up the chain as the registers reach (one hop); its directors and registered office; the Gazette; public
   office and political money; what is not held (sanctions lists, limited partnerships, overseas registers, trusts and
   the securities register, each named).
2. **The rules** (`rules.py`, 19 flags, contract bound by the shape, no import):
   - `holding-chain` names each company holder with its filed shares and files, then stops. The depth limit is
     `CHAIN_DEPTH = 4`; the registers reach `CHAIN_REACHED = 1`.
   - `ultimate-holders` and `sanctions-lists` are blocked from every start, never clear.
   - `custodial-holders` shows a nominee, trustee or custodian as a holder of record and nothing more.
   - `holder-hubs`, `partnership-holders` and `overseas-holders` fire on what they see and otherwise block.
   - Also: `public-office` (the domestic list of politically exposed persons), `political-money`, `company-status`,
     `insolvency-notices`, `prohibition`, `bankruptcy`, `young-entity`, `officers-of-record`, `namesake-exposure`,
     `walk-coverage`, `subject-hub` and `securities-register`.
   - From a company start, the people checks block.
3. **Tests.** Fast: 33 tests on fixtures, among them a mutant check that breaks the rules 15 ways. Every mutant is
   caught. Slow: two memos on real tables, with subjects chosen at run time. `bin/fast products/templates` is green.
4. **The checkpoint**: twelve real subjects (`checkpoint.list`), read against `pub.shareholders` and `pub.companies`.
   - None was refused by the presentation rules, and each built in under 7 s.
   - It found four faults, each now fixed with a property and a mutant:
     - "Corporation" and "Inc" were read as overseas (ACC; incorporated societies).
     - Near donations let `political-money` clear (RANK GROUP LIMITED).
     - A short walk let `custodial-holders` and `political-money` clear.
     - Decimal share counts printed "no share count filed".
   - `limits.md` holds the page and the table.

## Carded (not worked)

- `the-walk-does-not-follow-a-company-holder-up-the-chain`: for the report and companies lanes. This is the chain walk.
- `the-shareholders-view-carries-no-parcel-or-issued-shares`: for companies. No fraction, so no 25% line.
- `a-holders-count-of-companies-is-not-read-for-a-hub-flag`: for report.
- `the-catalogue-names-no-overseas-registers-or-trusts-as-not-held`: for report.
- `node2-lost-its-wired-link-and-an-orphaned-links-load-holds-its-locks`: a blocker for Arthur and the integrator. See
  below.

## For the integrator

- `docs/board.md` in the working copy was rewritten by the root generator test. It is not committed; regenerate it.
- The checkpoint ran on `pub.links` of 2,614,679 links, after your 07:50 reload failed. Re-render `checkpoint.list`
  once the links are reloaded.
- node2's wired ports have had no carrier since 07:50:59, so 10.0.0.2 and 10.0.0.10 are gone. This session read the
  database through 127.0.0.1 (`PGHOSTADDR`) with the session reader. The orphaned COPY backend that held the links
  locks ended by about 09:13.

Lesson: `a-clear-must-check-the-walk-reached-what-it-clears`.

## Result (integrator, 2026-10-21 10:44 NZDT)

Merged into main as 344bf44 (merged main first). Done at the merge: the
lesson `a-clear-must-check-the-walk-reached-what-it-clears` cut from 320 to
237 characters for the index; the blocker card
`node2-lost-its-wired-link-and-an-orphaned-links-load-holds-its-locks`
closed (addresses back 08:57 by the NetworkManager drop-in, the two
orphaned backends ended 09:13, links reloaded 09:00 to 09:25; the 10 Mb/s
question stays with the carrier card); the twelve checkpoint subjects
re-rendered on the 09:25 links (2,815,621): all twelve print, none refused,
under 7 s each; `qv4-report` restarted (the template is served from
disk); board, lessons index and queue regenerated. The four lane cards
(the chain walk, parcels and issued shares, a holder's company count, the
not-held catalogue) stand open for the report and companies lanes. No
profile, catalogue or job change.
