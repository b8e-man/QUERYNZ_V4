# Three by-elections and two 2020 electorate pages are not held
kind: finding
state: open
use-case: 1
session: house
opened: 2026-10-20

The results site answers automated reads with a challenge, and a
challenged read is a failed read (hard limit 6). What the old estate holds
of it is therefore partial, and the lane records each gap in its catch
log rather than filling it:

- **Port Waikato 2023** (by-election 25 November 2023, after the general
  poll was cancelled): the old job kept only the challenge page. So the
  2023 House is 122 members in `pub.members`, equal to the Commission's
  official result, and the 123rd (the by-election's winner) is missing.
- **Hamilton West 2022 and Tauranga 2022**: never captured. The 2020
  members for those seats carry a window ending, at the latest, on the
  by-election's polling day (from the results index); their successors
  are missing.
- **Mana and Rongotai 2020**: the old job's browser failed before the
  page loaded (`fetch error`). Both electorates and both members are
  published; their candidates and votes are missing (581 of the 2020
  electorate candidates read, from 70 of 72 pages).

The unlock is a read the site does not challenge (a headed browser shown
no challenge, as the capture rules allow), or the Commission's own
spreadsheets on request: Arthur's call. Nothing is fetched from this lane
before the switch.
