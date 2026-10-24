# The site build's compare gate counts a donor fold or a key change as a fall, so the build was refused four days running
kind: finding
state: open
use-case: Follow the Money; step 4.4 (the gates), 4.5 (the comparison's clean days)
session: integrator
opened: 2026-10-23

Found on 23 October 2026 reading the worker's journal. `qv4-site-build`
(08:00 daily) has been refused by a gate every day since 20 October, so
no version was accepted and step 4.5's count of clean days never started.

1. **20 October 20:04, 21 October 08:53, 22 October 08:00: the `compare`
   gate.** It reads every donor page's total in the version built before
   and refuses when any fell, unless the build is told `--allow-drop`. The
   20 October fall (`990 → 911 donor pages; 641 total(s) fell
   ($19,426,981.45), 711 page(s) gone`) is the donor key changing form at
   `site-3` (the `filed:` prefix and punctuation went: 613 of the 711 gone
   pages reappear under a new key with the same total to the cent) and
   the links' re-read display names after the rebuild of ruling 73; the
   sum of all donor pages moved from $29,675,901.68 to $29,555,901.68. The
   22 October fall (3 totals, $72,502.30, 193 new pages) is three pages
   renamed the same way, each total higher under its new name (checked
   25 October: ajr finance ltd $55,000 → ajr finance limited $75,000;
   craig shayne greenlees $10,000 → greenlees craig shayne $63,000; vanessa
   weenink $7,502.30 → weenink vanessa $33,859.50), with ruling 71's window
   (2017 onward; the sum rose to $34,045,287.22). Ruling 66, named here
   on 23 October, is the reconciliation doctrine and not a cause.
   The money gates that read the Commission's own tables (`commission`,
   `candidate-money`) were green on every one of those builds, so the
   figures stood; only the page keys moved. The gate cannot tell a fold or
   a key change from a loss, and `previous` is the newest version on disk,
   refused or not, so the next build compares against a refused one.
2. **23 October 08:00: the `commission` gate.** `pub.disclosures` cites
   the Commission's two index pages, which the old estate's job re-fetches
   nightly at 03:34, so their hashes change most nights; the lane has no
   load job, and the build left out 421 of 421 disclosure rows as citing a
   document the release listing does not hold. Reloaded by hand at 08:35;
   the nightly load is `fix-registers-disclosures-1`.

25 October 10:04: Arthur ran the build with `--allow-drop`; version
`2026-10-25T1004` accepted, nine gates green, 1,102 donor pages, the three
renamed pages present. The nightly build now compares against an accepted
version. The design ask below stays open.

The build with `--allow-drop` is Arthur's run, as the gate intends (the
integrator's hand run was refused by the session's permission classifier;
the accounting above is what the flag is told for). Asked of the
`products/published_site` module: compare money by cited row, not by
page key, so a fold is not a fall and a vanished row is; and compare
against the last accepted version, not the newest refused one.
