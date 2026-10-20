# site-1: the published-site shape and the Follow the Money template (plan 4.4)
branch: session/site (pushed; 39539a6)
session: site (session 1, Fable)
raised: 2026-10-20
claims: products/published_site/ (build, paths, pin, read, figures, render, redact, gates, version, preview, check, jobs-proposed.toml, units/, spec.md, tests/); products/templates/ftm/ (ftm.json, the loader, tests/); docs/status/site.md; three cards; one queue question; one lesson

The old release pipeline's shape behind the new contract, without its
last steps. `python -m products.published_site build` reads the 22 pub
views the template names (and nothing else: `Tables.get` refuses a view
the template does not name), pinned to a frozen release's listing from
the watcher (a money row citing a document the listing does not hold is
left out and counted), renders the ten kinds of published file by the
frozen site's own path rule (slug + FNV, pinned to its file names), writes
`<out>/v/<stamp>/` with `SNAPSHOT.json`, runs six gates, appends a
`built` row and stops. No deploy step, no token, no feedback, no
publisher unit, no port 8300 or 8301: `tests/test_ties_cut.py` reads the
package's syntax trees for every one of those names and ports.

The six gates: snapshot (manifest ↔ folder both ways, only the ten kinds,
no factory surface), addresses (every string of every payload sniffed for
a street, box or rural delivery; names the file and field, never the
text), suppressed (the list from `pub.suppressed_names` when a lane
publishes it; empty today, carded), donor fold (one donor, one page, every
row a party page shows on exactly one), commission (the one figure from
outside the estate: the Commission's table re-summed by SQL through the
connection, not the figures' code path; 46 party-years and the open year
equal to the cent), compare (the before-and-after arm against the last
*built* version; a fallen donor total refuses unless `--allow-drop`).
Each is shown failing on a planted defect in `tests/test_gates_can_fail.py`.

The template applies the window (2017, as the frozen site stands and
design.md fixes it; the brief's 2019 is a queue question with default
2017), the races (361/363/366), the seven parties by registration key,
"the return is the record" (a disclosure the return covers is sighted and
never added), ownership as a note, no press row, no address, a suppressed
name suppressed with the money kept.

Real build on `querynz_v4` from listing 2026-10-20T0620: 3,332 files
(home, parties, electorates ×5, pickers, subject party ×30 and person
×1,261, electorate ×82, donor ×623, size-bands ×27, cite ×1,300;
board-member "not held", no lane), 8 MB, 0.9 s end to end, every gate
green. 86 of 125 front-page party-year figures equal the frozen home file;
the rest are the lanes' carded differences (Labour 2017, NZ First 2019,
National 2022's two returns, Te Pāti Māori 2021) and Part A rows not yet
read (38 of 152 returns). Preview: `python -m products.published_site
preview` (8430, local network; the last built version).

For the integrator: append `jobs-proposed.toml` to the catalogue
(`qv4-site-build`, daily after the watcher's listing) and delete it; the
preview unit waits on the installer reaching `products/*/units/` (the
board's card); register `products.published_site.check.check` on the
board; `QV4_SITE_OUT` defaults to `<live>/site`.

Fast tier: `products/published_site` 44 passed, `products/templates` 8
passed (0.2 s each). Whole repository (243 s): green but
`tests/test_generators.py` (the three new cards make the board stale; the
integrator regenerates it) — the one-way import test was red on the first
run (the shape imported `products.templates`) and is green at 1a2e130: the
shape reads its template file itself (`site_template.py`).
Lesson: `lessons/none-chosen-is-a-property-of-the-year-not-of-the-headline.md`.

## Result (integrator, 2026-10-20 11:33 NZDT)

Merged into main as 39ccf01 (merged main first; the folder is
`products/published_site/`, since a folder named `site` clashes with
Python's own). Done at the merge: `qv4-site-build` in the catalogue
(priority 51, due 19:00 UTC, after the watcher's listing) and the
proposed file removed; the installer's unit globs reach
`products/*/units/`, and `qv4-site-preview` is installed and active on
10.0.0.2:8430; a lesson's rule cut to the limit; records regenerated.
Fast tier and gate green. Built once from the main checkout after the
merge: `<live>/site/v/2026-10-20T1134/`, every gate green; the scheduler
ran the due job at 11:23 as well. Registering the shape's check on the
checks board is carded for the comparison session
(`the-lanes-checks-are-not-on-the-checks-board`). The window question
(2017 or 2019) is in the queue with its default. The session ran
headless from the integrator as Fable, about 50 minutes.
