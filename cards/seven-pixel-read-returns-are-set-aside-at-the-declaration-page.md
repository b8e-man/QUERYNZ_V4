# Seven returns read from pixels are set aside at the declaration page
kind: finding
state: open
use-case: 1
session: party-returns
opened: 2026-10-19

Of the 74 returns whose image pages all have stored readings, 67 read to a
row and these seven do not, each with its reason in `party_returns.set_aside`:

- NZ First 2019 (`ea8b4bbbe195`): the parts read sum to $369,535.17 and
  the printed total is $368,535.17, which is the frozen site's figure. One
  part is misread by a digit; the total is right but unproven.
- TEA Party 2020 (`53b9663181c4`), Vision NZ 2022 (`380df5ce2adf`), NZ
  Outdoors & Freedom 2024 (`19156e3990b5`): the total is read and no part
  is, a layout the pixel reader does not yet pair.
- NZ Outdoors and Freedom 2021 (`9a69f1b198b7`): no total read.
- Social Credit 2019 (`794ddfdbfd8f`), New Conservative 2022 unaudited
  (`ea38362821ab`): no page states the year by the two rules.

Only NZ First 2019 is a front-page party-year. Not worked here. A page
reader's second look at one page is the likely fix for the first, a
layout case in `pixels.read` for the next three.
