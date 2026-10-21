# The report shape and five templates still say the Charities Register is not published
kind: finding
state: open
use-case: 2 3 4 5 6 7 8
session: founding
opened: 2026-10-21

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
