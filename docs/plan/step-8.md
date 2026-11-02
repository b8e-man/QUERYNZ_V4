## Step 8: the use cases' open parts

**Goal.** Close what the use cases still cannot see, as measured on 2 November 2026: the registers held but not read, the
reaches the walk stops short of, the registers not held, the scan's open red, and the start of archive search. Each part
below is one session in its own folder, so the parts run in parallel and merge one at a time.

**Why now.** Arthur, 2 November 2026: "let's plan out the build of these things like the original v4 build plan then run the
builds in paralell". The morning's work published the October companies package (insolvency appointments, retirement
villages), the Gazette after 20 October and its office families, the Real Estate Authority's decisions and the councils'
registers; the templates read only some of it.

**Models.** Opus for every part. A part that reads documents uses the local text reader (rulings 128 to 130), never a cloud model.

### Do

**8.1 The templates read what is published** (`products/report/`, `products/templates/`). The use cases 2, 3, 5, 6, 7, 8, 11, 12, 13.

- `pub.company_insolvencies` (109,586 appointments): the subject company's own, and each followed officer's other companies'
  (near, the officer's). The rules that today read only Gazette notices for a company's failure (repeat-insolvency,
  phoenix-signature, sister-company-failure, people-failed-companies, officer-group-insolvency) read the appointment too,
  dated by `appointed_on`; an appointee is an insolvency practitioner acting professionally, shown by name.
- `pub.retirement_villages` (514): healthcare (11) reads a company's villages by `operator_key` (confirmed) and the
  statutory supervisor; `retirement_villages` leaves `NOT_HELD`.
- The Gazette's office families (`pub.gazette_appointments` with `action`, `locality`, `appointee_kind`;
  `pub.gazette_board_interventions`): recruitment (8) and legal (2) list a subject's judicial, JP and statutory-manager
  appointments (near, by name unless a link confirms), never the town as an address.
- The walk's one step further for legal and banking's shared-boards: the other officers of each followed officer's companies,
  listed beside the officer, near; the limit and the omitted count stated.
- Each template's known-limits page says what it now reads. Verify on real rows: three companies with insolvency appointments
  and directors who have others; one village operator.

**8.2 Two links rules measured for Arthur** (`links/`). Rulings 105 to 109: measure, 20 pairs, Arthur rules, then a versioned rule.

- A member's declared interest (`pub.mp_interests`) to the company it names: by the name the return prints against the
  companies file; measure the join, set out 20 pairs, the counts by kind.
- A charity officer (`pub.charity_officers`) to a director or society officer: name plus a shared body (the charity's business
  number equals a company the director sits on, or the officer sits on a society of the same number); measure, 20 pairs.
- Nothing is applied to `pub.links` until Arthur rules. The pairs and the counts go to `docs/research/links-2026-11-02.md`.

**8.3 LINZ** (`registers/linz/`, new). Use cases 4 and 12.

- Survey LINZ's open data (the LINZ Data Service): which layers carry title, owner and parcel, their licence (CC BY 4.0 and
  the title-owner conditions), the size, the update cadence, and whether a key is needed (a key we register for is ours; a
  login that is not ours is never used, hard limit 6).
- Build the lane on the bulk export, landed by hash: titles (title number, type, status, land district, issue date), owners
  as the layer names them, and the official place names. The licence's conditions on individuals' title rows are applied
  as the layer states them; no home address of a person is published (hard limit 15): a title's parcel is a place, an
  owner is a name.
- `pub.linz_titles`, `pub.linz_title_owners`, `pub.linz_place_names`, with the outside check against LINZ's own counts.

**8.4 The Insolvency Register and the PPSR, surveyed** (`registers/insolvency/`, `registers/ppsr/`, new). Use cases 2, 5, 12, 13.

- The Insolvency and Trustee Service's register (personal bankruptcies, no-asset procedures, summary instalment orders,
  after the Gazette stopped printing them in December 2018): what a search returns, whether a bulk file or interface exists,
  terms, whether a challenge or a login stands in front; the Personal Property Securities Register likewise (search fees,
  the account it needs).
- Write each one's position (`docs/legal/positions/`), the four questions of hard limit 4. Build a lane only where a polite
  open read exists; where a fee, an account or a challenge stands in front, record it, card it, and stop.

**8.5 The scan's open red and the lobbying template** (`products/scan/`). Use cases 9, 10, 15.

- The procurement read-back red: the scan's check reads links that have since been rebuilt; mend it so the scan reads the
  links as published and the check is green on the live database.
- Use case 15, lobbying, step 6.2's fourth template, part (a) and (b): the ministers' diary entries
  (`pub.minister_diary_entries`) each meeting's organisations resolved to the registers (companies by name, near; a
  confirmed link where the links lane has one), and what each organisation is (donor, contractor of record, lobbying
  firm by its own register rows); a known-limits page that says backbench MPs publish no diary.

**8.6 Archive search, its first two parts** (`registers/papers_past/` and `products/archive/`, new). Use case 16; step 7.1 and 7.2.

- 7.1 first: the search-only rule with its test, so nothing from Papers Past can reach `links/` or `pub.names` (hard limit 17).
- 7.2's first batch only: ten thousand items, with the named stages, each with its count, and the catch log; in equals out
  plus set aside. Measure the disk each stage takes and project the whole archive; stop and report before a hundred
  thousand if node2's free space would fall under the limit.

**8.7 The councils' minutes** (`registers/council_minutes/`). Use cases 9, 14, 15. In flight: attendance, resolutions and
declarations, read and sampled; merge, then the full read is queued.

### Done when

- [ ] 8.1: every template reads the published registers it names, its known-limits page agrees with its reads, and the
      real-row checks fire where the rows say they should.
- [ ] 8.2: two measurements and forty pairs are in front of Arthur.
- [ ] 8.3: LINZ's titles and place names are published and checked against LINZ's counts.
- [ ] 8.4: two positions written; a lane where one is open; a card where one is not.
- [ ] 8.5: the scan's check is green on the live database; template 15 has had its checkpoint.
- [ ] 8.6: the search-only rule is tested; the first batch reconciles; the projection is written.
- [ ] 8.7: merged and queued.

### Brief to paste

```text
You are a build session for QueryNZV4 on node2, in a worktree of the main checkout. Read docs/plan/step-8.md and do part
8.N only, in its folder only. Hard limits as CLAUDE.md states them; a person's home address and a suppressed name are never
printed into this session, a card, a log or a commit (mask samples before you print them). Profiles before readers, pinned
both ways; new profiles go in the lane's proposed file and are appended to support/profiles/profiles.jsonl with the count
pin bumped (the integrator resolves the pin). A job's priority is unique (support/scheduler/jobs.toml; check the unused
numbers). Tests, one mutant per changed rule (edit back, never git checkout), the folder's suite green. Build into staging
and stop: do not publish to pub.*, do not install units, do not push. Commit on your branch with the Co-Authored-By line.
Finish with a terse report: branch, commit, what was built, counts on the real data, what is carded, what is left.
```
