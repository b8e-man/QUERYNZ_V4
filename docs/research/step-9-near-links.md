# Step 9, tranche 8: near links on request

Stream C of the step 9 integrator session, 9 November 2026. Ruling 151: the
first report follows confirmed links only; near links are followed on
request from it. Ruling 148: a near line says why it is near, and a name
that does not fully match may be another rendering of the name.

Built here, all new files:

- `products/report/near.py`: the second pass. `stage2(conn, report)` takes
  a finished first report and returns a copy with one more section,
  `near_on_request`, and `report["stage2"]`, the counts.
- `products/report/near_server.py`: the hook for the page (`render`,
  `asked`, `href`, `offer`). The server does not call it yet; see Wiring.
- `products/report/tests/test_near.py` (fast) and `test_near_real.py` (slow).

## 1. The near links the estate holds

### Stored by the links lane: `pub.links`, grade `near`

`pub.links` has columns `link_id, row_a, row_b, rule, evidence, grade,
reason, watch, decision, built_at, relation`. Its reason is in `reason`.
A pair that a decision marks `not the same` or `contested` shows as near
with the decision as its reason. Counts are from `bin/q`, 9 November 2026,
on a links build of 08:32 that day.

| Rule | Near rows | What the reason says |
| --- | ---: | --- |
| `name-only@1` | 5,948,066 | same first and last name: no middle name to compare (2,160,157); only one gives a middle name (1,295,190); a LINZ owner's name alone (1,078,811); the middle names differ (939,089); a politician needs a supporting link (45,841); contested by a decision (3); **blank (428,975)** |
| `owner-full-name@1` | 2,217,361 | a LINZ title owner's full name alone, with no title or address to back it |
| `organisation-name@1` | 1,000,316 | a name match on a register of bodies with no official number on the row; split by which registers, how many bodies have the name, and undated |
| `full-name@1` | 572,669 | a name a text reader's model read (its own tier, 1 November) |
| `organisation-sole-company@3` | 157,997 | a name a model read (157,893); the row prints another body's number (104) |
| `company-name@1` | 88,509 | two companies under one name (75,785); the same apart from a year in brackets (12,724) |
| `organisation-one-live-company@3` | 29,094 | a name a model read (29,082); another body's number (12) |
| `member-on-the-day@1` | 21,533 | a member of the name sat in the House, but not on the row's day |
| `judgment-address-title@1` | 5,953 | addresses agree but no name is shared (3,054); no place on both (2,559); a model's reading (340) |
| `judgment-address-judgment@1` | 4,751 | no place on both (3,663); a model's reading (1,072); no name shared (16) |
| `shared-contact@1` | 531 | one email or phone beside two names that differ (465); a model's reading (66) |
| `filed-name@1` | 352 | two donation rows under one organisation name, no official number |
| `judgment-address-office@1` | 248 | an office shared by more than five companies (94); a model's reading (80); no party of that name in the document (74) |
| `candidate-name-form@1` | 180 | one name printed two ways for one party |
| `member-and-party-donor@1` | 110 | a politician's name on a donor row to their own party |
| `coupled-name@1` | 84 | one of two people the Commission filed on one donor line |
| `judgment-number@1` | 73 | a model's reading (70); the body's number with a name its registers lack (3) |
| `licence-number@1` | 31 | one licence number beside two names that disagree (29); a person and an agency (2) |
| `judgment-address-insolvency@1` | 13 | no name shared (9); a model's reading (4) |
| `own-return@1` | 1 | the candidate's own name as a donor on their own return |
| `lbp-number@1` (ruling 148) | **0** | coded (`links/rules.py` `NEAR_LBP_SURNAME`, `NEAR_LBP_NAMES`, both saying the name may be "another rendering") but **not yet in `pub.links`**: no links build has run since it was added. Stage 2 carries its reasons word for word once it is published |

Total near: 10,047,872. The `related` grade (974 rows, `successor-name@1`
and `refiled-name@1`) is not near (ruling 106 (2)). It keeps its own
section in stage 1 and stage 2 never reads it.

`name-only@1` is stored as a star (links/spec.md, the contract for
readers). Stage 2 reads each star through its centre (`walk.star_links`),
so the rows listed never depend on which row the lane made the centre.

### Name joins made by the report itself (`products/report/walk.py`)

Some views no link reaches yet. For these the report matches a confirmed
person row by name and grades the match near, with the view's own reason:

- `walk.NAME_JOIN_TO`, rule `same-name`: charity officers, Building
  Practitioners Board decisions, WorkSafe, Commerce Commission, FMA and
  Overseas Investment Office parties, roles and past holdings from the
  business-number register, Real Estate Authority decisions, councillors'
  interests, Gazette appointments.
- `walk.NAMED_ROWS`, rule `printed-name`: the MP and minister expense
  releases, by printed name.

These rows are matched at run time, so they have no stored count. Stage 2
runs both joins (`walk.name_joined`, `walk.named_rows`) from the
first report's confirmed person rows.

The walk also has near reaches that are not name matches: through two
people (`second`, `beside`, `officers`), a shared office (`office`), and a
holder of record matched by name (`chain`). Those are stage 1's
business (stream B), and stage 2 does not repeat them.

## 2. What stage 2 adds: measured on real subjects

Diagnostic template. The current stage 1 still lists near rows, so the
measure removes them first to give a first report with only confirmed
rows, as ruling 151 has it, then runs stage 2. Times are on node2 with the
session reader.

| Subject (row ref) | Stage 1 confirmed | Stage 2 near | By kind | Left out | Stage 2 time |
| --- | ---: | ---: | --- | ---: | ---: |
| `companies:companies/9429030982376/director/6b835e22f9ed` | 4 | 1 | name-only 1 | 0 | 0.5 s |
| `charities:charities/officers/1657104` | 19 | 3 | name-only 3 | 0 | 0.4 s |
| `linz:linz/owners/4184271` | 2 | 94 | name-only 93, owner-full-name 1 | 0 | 13.9 s |
| `party_returns:5d2a41e2…873b528c/A/10` | 2 | 36 | name-only 36 | 0 | 0.8 s |
| `companies:companies/9429050824540/shareholder/ca09d19615b4` | 11 | 9 | name-only 8, company-name 1 | 0 | 1.8 s |
| `societies:societies/9429042575801/officer/fcb70ceb47b9` | 6 | 200 | name-only 190, owner-full-name 6, same-name 4 | 0 (38 already listed) | 24.2 s |
| `building_practitioners:…/decision/CB26157/decision` | 1 | 0 | none (lbp-number@1 not yet published) | 0 | 0.0 s |
| `beehive:0631b625…88d2bb11/person/13` (a star centre, 12,366 spokes) | 1 | 400 | name-only 256, full-name 144 | 25,877 | 43.6 s |
| `beehive:08193622…347bfdf5/person/1` (a spoke of that star) | 1 | 400 | name-only 399, full-name 1 | 11,966 | 49.4 s |

Where it swells:

- **`name-only@1` stars.** Every large count comes from them. A person
  whose first and last name are common reaches the whole star: up to
  12,366 rows from one centre, nearly all press-release (`beehive`)
  rows. The other big source is LINZ owners (`owner-full-name@1` and
  `name-only@1`'s "LINZ owner's name alone").
- **The limits hold it.** Stage 2 reads at most 600 stored near links
  (`near.LIMITS["links"]`), plus the star's 400 (`walk.LIMITS["star"]`),
  and lists at most 400 rows (`near.LIMITS["items"]`). Each row it lists
  costs a few reads, so on a star the pass takes about 45 to 50 s. What
  it leaves out is counted and printed, never silent. The order within
  the limit is the rule, then the row's ref in byte order. Nothing is
  ranked by size or fame.
- For ordinary subjects (a director, a charity officer, a shareholder)
  stage 2 adds 1 to 9 rows in under 2 s.

## 3. The guarantees and their tests

- Every stage 2 row is graded near and has a reason. The entity a near
  row sits on (its company, its return) is near too, with the reason
  "reached through a near link: …". The first version listed those
  entities as confirmed, and the guard below caught it on the first real
  run (`linz:linz/owners/4184271`: 6 added).
- **Guard:** `stage2` raises if the confirmed set after the pass differs
  from the first report's. It reads every section, its own included.
  `test_a_near_link_never_enters_the_confirmed_set` gives it the walk's
  confirmed-graded rows and entities. Run against a version that leaves
  the grade as the helper made it, the test fails (checked).
  `test_the_guard_refuses_a_confirmed_item_in_the_second_pass` shows the
  guard is not silent.
- The first report is left unchanged (deep comparison). A row it already
  lists is not listed again, and the count is kept. Running the pass
  again replaces its section instead of adding a second one.
- A blank stored reason never reaches the page. `near.reason_for` falls
  back to the rule's own wording (presentation rule 8).
- The presentation rules (`rules.problems`) run again on the whole
  report. They found no problems on any of the nine subjects.

Tests: `test_near.py` 10 passed; `test_near_real.py` (slow) 1 passed;
`products/report/tests -m "not slow"` 125 passed. The one failure in
`tests/test_imports_one_way.py` comes from the existing
`products/report/tests/test_retired_templates.py`, which imports
`products.board`. It is tranche 1's file, not this tranche's.

## 4. Wiring: the change for stream B or the integrator

These are three small edits to `products/report/server.py` and one to
`products/report/memo.py`. Nothing in `near*.py` needs to change.

1. `server.py`: add `near` to the page's own query names, so the builder
   does not refuse it as an undeclared template parameter:

   ```python
   QUERY_OWN = frozenset({"ref", "template", "format", "m", "saved", "since", "q", "near"})
   ```

2. `server.py`, in `do_GET`'s `/report` branch, before the existing
   `render(...)` call:

   ```python
   from products.report import near_server   # at the top, with the other imports
   ...
   if near_server.asked(qs):
       ctype, body = near_server.render(ref, get("template", "subject"), get("format", "html"), get("m")[:100],
                                        get("saved") == "1", since=get("since")[:10], params=query_params(qs))
   else:
       ctype, body = render(ref, ...)          # as now
   ```

3. `server.py`, in `render` (the stage 1 HTML branch): put the link on
   the first report by adding the offer line in front of the memo body:

   ```python
   body = near_server.offer(report, template_name, since, params) + memo.html_body(report)
   ```

   `offer` returns nothing for a report that was not found or is already
   stage 2.

4. Optional, `memo.py` `text()`: nothing is needed. The memo already
   prints every section, the near one too. `near_server.render` adds
   `near.summary(report)` (counts by kind, what was left out) to the end
   of the text form.

Saving: `POST /save` builds stage 1 only. Saving a stage-2 memo would need
`near` passed through the save form. That is left for B, because the save
form is in `memo.page`.

Stage 1 itself: ruling 151 says the first report follows confirmed links
only. Today's walk still lists near rows in stage 1 (`near`, `named`,
`second`, `beside`, the stars). Removing them is stream B's work. Stage 2
does not depend on it: a row stage 1 already lists is counted, not
listed twice.

## 5. Faults found, for the links lane

- **428,975 `name-only@1` near links have no reason.** Their evidence is
  a full name with a middle name (`full_name`, `middle`, `as_filed`,
  `registers`). In the star builder (`links/build.py` near_links), when
  two components share a full name, `rules.judge` returns `full-name@1`
  as confirmed with reason `None`. The builder stores that pair as
  `name-only@1` near and keeps the `None`. The report covers it with
  `near.NO_REASON_FULL`, but the lane should store a reason. This is a
  card for the links lane. It is not raised in the inbox here, because
  this stream may write only new files.
- `lbp-number@1` (ruling 148) is coded but not yet in `pub.links`. It
  appears in stage 2 after the next links build. That build needs no
  change here.
