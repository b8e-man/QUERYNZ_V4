# The PPSR is searched only from an account and for a fee, so no security interest is held
kind: blocker
state: open
use-case: 2 legal counterparty and conflict check; 5 business credit; 12 property; 13 ownership
session: step-8-4
opened: 2026-11-02

Every PPSR search needs an online services account, a declaration that it is for a legitimate reason, and a fee ($2.30 on
the website, $1.15 through the API); there is no bulk file (position
`docs/legal/positions/personal-property-securities-register.md`). So no copy of the register can be held, and the templates'
`securities` key stays not held.

What closes it: Arthur's word on an account in the estate's name, a payment method and a budget; the lane would then search a
debtor organisation by NZBN on demand when a report asks (products rule 2), each answer landed and each fee counted.

3 November 2026: the account exists and its production API key is in the credentials folder (`ppsr.env`, `PPSR_API_KEY`,
header `Ocp-Apim-Subscription-Key`). Base `https://api.business.govt.nz/gateway/companies-office/ppsr/v2` (v1 and the bare
`/gateway/ppsr` answer 404; the sandbox key answers 401 there). The free calls `GET /customer-organisation` and
`GET /user-current` answer 200: organisation active, its one user an admin. Operation paths are in the portal's PPSR API
Business Rules (PPSR_02 search is `POST /financing-statements-search`). Still open: the direct debit authority a fee-bearing
call needs, and the budget.
