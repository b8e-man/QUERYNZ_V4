# Page sections the template does not carry
kind: finding
state: closed
use-case: 1
session: comparison
opened: 2026-10-20
closed: 2026-10-20

Whole sections of the frozen pages have no counterpart on the rebuilt
ones. Home: party transfers, race donations, race spend, party funding,
donor categories, party spend, race public money, promoter spend, donors
sighted (11 sections). Parties page: unaffiliated sitting members, junk
labels, unmatched disclosures. Party page: donations made, top donors,
rules, leaders. Person pages: positions, properties, industry exposure,
the interests tree, public expenses, party boards, donations made and
received (about nine sections on each of 1,228 pages, 10,637 in all). The
site's known-limits page says press, industry exposure, interests and
expenses are not in this template.

Which side is right: the frozen one, under the plan's goal of reproducing
it, until Arthur rules which sections belong to Follow the Money (queue:
`which-frozen-sections-belong-in-the-follow-the-money-template`, default
all of them). Owner: site.

Closed (site-2, 2026-10-20). Every section named here is on the rebuilt pages under the queue's default: the home page's eleven money sections
(party spend, public money and promoter totals equal the frozen to the cent; party transfers, race donations and race spend are short by the
candidate-returns lane's coverage and 2017), the parties page's three, the party page's donations made, top donors, rules and leaders (the last two
"not held" with why, in `party_window` where the frozen kept them) and coverage, the person page's positions, properties and other interests from
the member's own returns, donations received and made, and the interests tree, exposure, expenses and party boards as "not held" with why. The
template marks the person-page sections as the ones the queue's recommendation would move. Measured by `python -m checks.comparison run` against
the frozen 2026-10-20T0620, rebuilt in scratch: 10,651 differences fell to 266, all one key: the frozen page's `candidate_rows_gap` line is written
for a candidate with the Commission's total and no parsed return, a state the rebuilt side has no row for; its words are in the person page's
basis instead.

Ruling 68 (21 October): every frozen section belongs in the template; the comparison keeps counting a missing one against the new side until the template carries it. Not to be asked again.
