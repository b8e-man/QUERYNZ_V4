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
   the donor fold of `reconcile-1` (ruling 66) joining pages; the sum of
   all donor pages moved from $29,675,901.68 to $29,555,901.68. The 22
   October fall (3 totals, $72,502.30, 193 new pages) is the fold again
   and ruling 71's window (2017 onward; the sum rose to $34,045,287.22).
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

The build with `--allow-drop` is Arthur's run, as the gate intends (the
integrator's hand run was refused by the session's permission classifier;
the accounting above is what the flag is told for). Asked of the
`products/published_site` module: compare money by cited row, not by
page key, so a fold is not a fall and a vanished row is; and compare
against the last accepted version, not the newest refused one.
