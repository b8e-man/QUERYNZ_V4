## Step 4: Follow the Money rebuilt

**Goal.** Follow the Money running on the new estate and reproducing the frozen site, with every difference explained by a card.

**Why first among the products.** Arthur's ruling 15. It is also the one product with known answers for every part: the Commission's own totals for the registers, the frozen site for the pages.

**Models.** Opus for each lane. Fable for the links, the published-site shape, the comparison and the integrator. This is the first step that fans out: three sessions plus the integrator.

### What the frozen site is

- A static site on an outside host, with search running in the reader's browser and one small hosted function that takes feedback. With both boxes off it stays up as at its last release.
- It publishes ten kinds of page data, listed in `data-layer/pi/pi/snapshot_paths.py`: home, parties, electorates, pickers, subject, electorate, donor, board-member, size-bands, cite.
- The daily release (`ops/pi_release.py`, run by `ftm-release`) regenerates everything, runs its gates, and flips the site only on green. Publishing is in `ops/pi_cloudflare.py`; feedback is drained by `ops/feedback_pull.py`.

Holes already on record. Reproduce the frozen site first; then each of these is a finding card, not a silent fix.

- The donor list is cut at 1,500 before names are folded, so a donor can lose its page.
- A parsed return total was held for under half the party-years since 2019 at one count; measure it again.
- The announced-candidates tier is empty, and the 2026 candidate list has never been captured: the Commission's pages are behind a challenge.
- Parliament's Hansard pages have been behind a challenge since about 5 October; the Hansard register is held at 23 September. No technical route will be sought. The unlock is a permission request, which is Arthur's. Ruling 78 (21 October): no request is sent; Hansard is not captured, Arthur supplies a third-party source.
- No electorate candidate has a vote count: the results site refuses automated reads.

### Do

**4.1 Build the lanes, in parallel.** Each lane re-reads from documents already captured, taken by hash from the old `var/staging/` folders, read-only. Nothing is re-fetched that is already held, and until the public site is switched the old capture jobs stay the only fetchers for their sources. Decisions and corrections are copied across untouched. Each lane holds everything its source holds, back to the source's start; only the Follow the Money template applies the 2019 window. The folder name for each lane is listed under the briefs below.

Which of the three cases in step 1.10 each lane starts from, as far as the old repository shows. Confirm each in the baseline.

| Lane | Starts from |
| --- | --- |
| Party returns, candidate returns, disclosures, party finance, party register, party rules | Files held under `var/staging/` |
| MPs' and ministers' expenses; LINZ titles | Files held under `var/staging/` |
| Gazette notices; Hansard | Text rows in the old news database, no file. Export once |
| Companies and the other entity types | The monthly file Arthur downloads. Find where the raw files are kept; if only the loaded tables survive, export once |
| Charities | Parsed straight into tables from the register's own data feed; no file was kept. One capture of its own, shared by both builds of this lane |
| Society officers; MPs' interests | Find out in the baseline |

| Lane | Kind | Notes |
| --- | --- | --- |
| Charities register and officers | Copied | **Build this one twice, once with Fable and once with Opus, against the same tests, in two folders (charities-a and charities-b) from one shared set of captured files so nothing is fetched twice. Record the comparison and keep one.** The old lane's client bypassed the fetch gate and its host no longer resolves; take the idea (verbatim copy, then read), not the code |
| Companies, directors, shareholders, addresses, and the other entity types | Copied | The monthly file is downloaded by hand by Arthur and is not to be raised as outstanding. Sole traders, partnerships and trusts are not in it |
| Register of Political Parties, and party lifecycle | Copied and built | Renames come from registration windows: four are known. A renamed party is the same party |
| Party donation and loan returns | Built | The core lane. Uses the readers chosen in step 3 and the profiles. See "Electoral Commission forms" in the reference section before writing a line |
| Candidate returns | Built | Totals come from the Commission's own spreadsheet, joined on year, electorate and surname. Amended returns are republished under a different file-name pattern |
| Large-donation disclosures (over $20,000) | Built | Build this lane first. It is the one feed the frozen site still depends on, and once it reproduces the old feed it can take that feed over, on Arthur's word. The Commission states which declaration an amendment replaces; never infer it. Its listing often shows a challenge to plain requests. A headed browser that is shown no challenge may read it; shown one, it stops |
| Party expense returns, broadcasting allocation, party financial statements, promoters, party rules | Built | Each has a profile |
| Candidates, electorates, who sits in the House | Built | Electorate names join 72 of 72 to Stats NZ's. Boundary shapes need a key that is Arthur's to place |
| MPs' declared interests; MPs' and ministers' expenses | Copied from published files | The interests register renumbered its categories in 2018: key on the heading, not the number. Every edition reprints the rules after the last member |
| Gazette: party events, public appointments, insolvency, prohibitions | Built | The old lane's gate records a failure and still exits clean; do not carry that. 90.8% of its 35,938 unread notices are one celebrant format |
| Incorporated-society officers | Copied through the per-entity interface | A seventh of the societies each night, the party societies first |

**4.2 Build the links.**

- Take from the old estate the ledger and the two rules, not the hand-set weights. The pieces are in `data-layer/registers/registers/`: `donor_anchors.py`, `roster_folds.py` (the folds and the watch), `person_identity.py` (ordered resolution, never fused), `folds.py`.
- **Copy the old decisions across exactly as they are, into their own table, and never edit them.** Beside them, build a mapping from each old decision to the new stable keys of the two rows it was about. The old row numbers changed every night, so map by content: the names, the document, the amount or the role. A decision that cannot be mapped is carded, not guessed. The old verdict "hold" maps to "contested".
- Company shareholders are matched by name because the official number is empty on all 1.58 million rows; 26,857 had no match.
- Run the six first measurements and record them. None has ever been run:

1. How often a full name repeats, by how common the name is.
2. Addresses shared by many companies.
3. The error rate of the two confirming rules. No person labels this. Measure it on the test pairs from 4.3, and have the review agent read 100 confirmed links drawn at random with their evidence; report both figures and say plainly that the second is an agent's judgment.
4. How often each rule can fire at all, per register.
5. Company names to official numbers: the share that match exactly one company alive on the donation date.
6. The shape of the groups: sizes, and any group that contradicts itself.

- The error rate is recorded by name band on every rebuild. The acceptable number is ruled later by Arthur, with this data, before anything is sold or a new person-level connection goes on the public site.

**4.3 Build the test pairs from the registers.** No person labels them.

- **Known to be two people:** two directors with one name on one company at the same time; two candidates with one name standing in different electorates at one election.
- **Known to be one person:** the same role carried from one monthly company file to the next under the source's own role identifier; the same officer across a charity's successive annual returns under the source's own officer identifier; a candidate across an original and an amended return.
- **Size and sampling:** aim for at least 200 pairs of each kind in each name band (rare, middling, common), drawn at random within the band. Say so where a band cannot supply that many.
- **Use:** score the joining rules on them at every rebuild, and score the review agent on them before it acts alone (track C).

**Hold the director addresses from before 18 November.** The monthly company files captured before that date are documents and cannot be regenerated. Confirm the last one before 18 November is in the document store on both boxes and in the off-site copy. Add a check that fails if an address published after that date, where a director has substituted a service address, is used to confirm a link. The home addresses themselves are used for matching only and appear in no published table.

**4.4 Build the published-site shape and the Follow the Money template.** Move the release pipeline behind the new contract with its gates, **without its last steps**. The new pipeline stops when it has written a version folder. It has no deploy step, holds no deploy token, does not drain the live site's feedback, and serves its preview on ports other than 8300 and 8301. The old scripts have the frozen product's publisher job name and both of those ports written into them, and restart that job. Cut every one of those ties. Left in, the new pipeline would restart the frozen publisher and build the "new" site from the old app, and the comparison would pass while testing nothing. Add one gate that checks a figure from outside the estate, the Commission's own published table: on 3 October a fold took $8,024,342 across 110 donors off the old site and eleven gates passed it, because every gate read our own output.

**4.5 Compare with the frozen site.**

| Question | Answer |
| --- | --- |
| At what grain | Every published file of the ten kinds, figure by figure |
| Same inputs | At each frozen release the watcher records the version's name and a listing, by path and hash, of the captured-document folders. The new estate builds each day from that listing, so timing is not counted as a difference |
| Over how long | Seven consecutive daily releases |
| Tolerance | None on money. A difference is a difference |
| Each cause of difference | One card, saying which side is right and why. One card per cause, not per figure: rebuilt links over the whole director register will move many folds for a few reasons |
| A clean day | No difference without a card, and no card saying the new side is wrong |
| Passing | Seven clean days in a row |

**4.6 Checkpoint.** Run the product's checklist. Card what fails. Write the known-limits page. Fix, accept or drop each finding.

**4.7 Export test.** Build the bundle, start it with no connection to the estate, and run the product's checks.

**4.8 Do not switch the public site.** The rebuilt product replaces the frozen one only on Arthur's decision, not before 7 November, and by one change that can be undone. The old chain is disabled and kept.

**4.9 Build the board: the way to see connections across registers** (ruling 52). Arthur: "I would like an interface that lets me see the connections between registers. One problem is the difficulty visualising the data. It would be good to be able to run a search and see the results across registers displayed in panes like our Miller boards."

&#91;embedded content: the board · four panes, one path\]

**What it is.** A search box and a row of panes that grows to the right. The first two estates had this and called it the Miller board.

- **One search across every register at once.** The first pane lists the results grouped by register, with a count for each. A register that is not held says "not held".
- **Clicking a result opens a pane to its right:** the row, its fields, its source document, and its links grouped by register. Confirmed links come first and near links after, each with the rule that made it and the reason it is only near.
- **Clicking a link opens the next pane.** The row of panes is the path walked, left to right, so a connection across three or four registers is visible at once.
- **A person pane shows the group:** every row gathered as that person, by register, with the links that hold the group together, and the possible namesakes listed apart. A contested link shows its decisions.
- **A pane can be pinned, and a path can be saved.** From step 5 on, "report from here" opens a subject report on that row.

**It is a fifth shape, and it serves no single use case.** It is the way to look at the estate itself, for a customer and for the builder. It reads published tables, links and groups only. It creates nothing: no link is made by looking. Every pane cites its document, and every rule for what a product may show applies, home addresses above all.

**How it is built.**

- **A search table across registers,** published by `links`: one entry for every name, address and official number in every register, under the one shared reading, pointing at its row. It is rebuilt with the registers.
- **Each lane says how its rows appear in a pane,** as part of its spec: the title, the fields shown, the dates, the citation. A new lane's rows then appear on the board with no change to the board.
- **Take the mechanics from the earlier boards:** the panel chain in the oldest repository's `frontend/src/pages/SearchPage.tsx` with its `NzbnPanel` and `PersonPanel`; and in the old estate, `gui/src/pages/IndustryPage.tsx` and `gui/src/components/DossierView`. They are React and TypeScript.
- It lives in `products/board/`, on its own port, on the local network only.

**Why here.** It is the fastest way to see whether the links are right, so build its first version as soon as the first lanes and the links exist, before the comparison in 4.5. It grows with every lane after that, and in step 7 archive-search results become a pane too.

**Done when,** for this first version: a search for a known donor opens, across four panes, its returns, the company behind it, that company's directors, and one director's other companies, each pane citing its document.

### Done when

- [ ] Every lane has its five-line spec, its outside check passing, and a reconciling catch log.
- [ ] The Fable and Opus builds of the charities lane are compared and the result is a lesson.
- [ ] The six measurements are recorded.
- [ ] The comparison has run seven days with no difference lacking a card.
- [ ] The checkpoint is done and the known-limits page exists.
- [ ] The export test passes.

### Briefs to paste

For each lane (change the lane name and folder):

```text
You are a build session for QueryNZV4 on node2, running as the model
docs/briefs/next.md names, in the working copy the launcher made for
you. Read docs/PLAN.md, then docs/status.md and your own status file,
then the lane contract and the row contract. Build one lane only:
<lane>, in registers/<lane>/. Get its documents the way step 1.10
says for its case; fetch nothing the old estate already holds. Search
the lessons and the reference notes for this source before writing
anything. Give every row a stable key and a citation. Keep a catch
log that reconciles. Find one figure from the source itself to check
against. Work in your scratch schema; edit nothing outside your
folder; never touch the old estate's jobs, folders or primary
database. Push your branch and raise a merge request. Finish by
telling Arthur what closed and what is carded.
```

Lane folder names for this step: `charities-a`, `charities-b`, `companies`, `parties`, `party-returns`, `candidate-returns`, `disclosures`, `party-finance` (expenses, statements, promoters, rules), `candidates-house`, `interests-expenses`, `gazette`, `society-officers`.

For the links, the shape and the comparison:

```text
You are a build session for QueryNZV4, running as Fable on node2, in
the working copy the launcher made for you. Read docs/PLAN.md, then
docs/status.md and your own status file, and continue where it stops.
Do the part of step 4 named here: <links, in links/ | published-site
shape and Follow the Money template, in products/site/ and
products/templates/ftm/ | the board, in products/board/ | comparison
with the frozen site, in checks/>. The two confirming rules are exact
and are not yours to change. Copy the old decisions untouched and map
them beside. Record the six measurements. The new release pipeline has
no deploy step and never touches the frozen product's publisher job
or its ports. Do not switch the public site. Push your branch and
raise a merge request. Finish by telling Arthur what closed, what is
carded and what waits on him.
```

