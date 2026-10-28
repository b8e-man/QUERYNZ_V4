# Christopher & Banks Limited is not related by ruling 109's rule: the removed company has no people in the published register. How should it be reached?
default: Nothing changes: the pair stays near under `company-name@1` ("two companies under one name"), and `refiled-name@1` relates only pairs with a person confirmed on both
blocks: Nothing. The rule is built and relates 2 pairs; the case that raised it is not one of them
recommendation: (a). Ask the companies lane to fill `pub.company_lookup_roles` (the lookup of one company; its columns carry a role's status and its start and end dates, so it can hold a removed company's people; whether the lookup returns them for a removed company is for the companies lane to measure) for the removed half of each pair the rule could judge: 12,607 pairs of companies under one name, one removed and the other registered within twelve months, of which 5,559 have people on one company only. The rule then reads them with no change. (b), relating by the name and the dates alone, is what ruling 109 refused ("the name alone stays near")
raised: 2026-10-28 by fix-links-2 (ruling 109)

The published register keeps people for 3,360 of 1,099,638 removed
companies: a removed company keeps its people only where a monthly file the
companies lane holds still listed it. Christopher & Banks Limited 3482091
(registered 2011-07-28, removed 2024-12-18) has no director or shareholder
row in `pub.directors` or `pub.shareholders`, and `pub.company_lookup_roles`
holds no rows at all. So no person can be confirmed on both it and 9321019
(registered 2025-03-06). This is absence of evidence: the register as
published cannot see the people, not proof that none were shared.
The two pairs the rule did relate were both removed on 2026-07-31, inside
the lane's files (`links/measurements.md`, section 9).
