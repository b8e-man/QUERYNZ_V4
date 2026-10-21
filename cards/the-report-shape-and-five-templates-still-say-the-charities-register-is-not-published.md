# The report shape and five templates still say the Charities Register is not published
kind: finding
state: closed
use-case: 2 3 4 5 6 7 8
session: founding
opened: 2026-10-21
closed: 2026-10-21

`charities-3` published `pub.charities`, `pub.charity_officers` and
`pub.charity_returns` on 21 October 2026. The report shape's catalogue
(`products/report/catalogue.py`) still lists "Charities register and
officers" among the registers not held and knows no charities view, so no
template can reach a charity or its officers; every template's `rules.py`
that carries `CHARITIES_NOT_HELD` ("the Charities Register and its officers
(not yet published)") blocks `charity-officer-roles` and
`charity-integrity-marks` on that ground. Both flags can now run: the
officer rows carry the register's `disqualified` mark and the roles.

Owner: report (the catalogue: three views, their reaches from a person's
name and a company's NZBN, the not-held entry removed), then each template
(the two flags rewritten to read `charity_officers`; `CHARITIES_NOT_HELD`
gone). Not a comparison cause.

Closed for the report shape (fix-report-2, 2026-10-21). The catalogue
knows `charities`, `charity_officers` (names suppressed where the row says
so, the register's `disqualified` mark in the statement, a withheld name
field as the row's note) and `charity_returns` (dated "period to", the
figures as filed); the register is listed among those held and is no longer
in the not-held list. The reaches: a company's charity by its business
number (an entity of the walk, confirmed, rule `official-number`, with the
company's grade), the charity's officers and returns beneath it (returns
newest first), a charity officer's charity as its entity, and a charity
officer that carries a person's name (a director, a society officer, a
member, a candidate, an interests return, a promoter's person, an
appointee) listed near by name with its reason, because no link joins the
register yet (card `charity-officers-are-in-no-link-and-no-name-row`, links
lane). The subject template reads the three views (CC BY 3.0 NZ, Charities
Services) in a charities section. A template that still names `charities`
in a section's `not_held` loads: the key is dropped from its blank and the
memo says the register is published and the template does not read it.
`python -m products.report check` runs the routes on run-time rows. The
templates' half stays open in each template's own card: the two flags
rewritten to read `charity_officers`, `CHARITIES_NOT_HELD` and the
`not_held = ["charities"]` lines gone, the three views in `reads`.
