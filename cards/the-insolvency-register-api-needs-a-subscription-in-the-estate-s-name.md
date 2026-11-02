# The Insolvency Register API needs a subscription in the estate's name, so personal bankruptcies after 2018 are not held
kind: blocker
state: closed
use-case: 2 legal counterparty and conflict check; 3 banking director history; 5 business credit; 6 insurance; 7 construction; 8 recruitment; 12 property; 13 ownership
session: step-8-4
opened: 2026-11-02
closed: 2026-11-03

The Gazette stopped printing its weekly bankruptcy and no-asset-procedure lists in December 2018, so the Insolvency Register
is the only source of a person's insolvency since (position `docs/legal/positions/insolvency-register.md`). Its public
search is one name at a time; the bulk path is the Insolvency Register API on the MBIE API portal, which serves authorised
users only: a subscription to its product, which the portal's support team approves. The estate's NZBN key is for another
product on the same portal.

What closes it: Arthur subscribes the estate to the Insolvency Register API product (portal.api.business.govt.nz, product
"insolvency-register") and puts the key in the credentials folder himself. The lane then polls the date-range search and the
removals-and-corrections call daily and applies the register's retention windows (position, question 4).

Closed 3 November 2026: Arthur placed the key in the credentials folder on 2 November (ruling 135); the lane's live test
saw 1,180 estates in 18 calls after the /v5 path fix (44949bb), and the nightly run starts at 21:00 NZDT.
