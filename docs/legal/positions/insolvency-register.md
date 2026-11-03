# The Insolvency Register (position, hard limit 9)

hosts: www.insolvency.govt.nz, insolvency.govt.nz, portal.api.business.govt.nz, api.business.govt.nz

Class: the Insolvency and Trustee Service's public registers (Ministry of Business, Innovation and Employment): the Insolvency
Register (current bankruptcies, no asset procedures, liquidations the Official Assignee administers, and bankruptcies and no
asset procedures discharged less than four years ago) and the Debt Repayment Order Register. Since December 2018 the Gazette
prints no weekly bankruptcy or no-asset-procedure lists (step 8.4; the Gazette fork's count, 2 November 2026), so for a
person's insolvency after 2018 this is the one source. A company's insolvency appointments come from the Companies Office's
monthly file (`pub.company_insolvencies`), not from here. Surveyed 2 November 2026 by step 8.4, seven gated requests in all.
Subscribed 2 November 2026 on Arthur's word; the lane is `registers/insolvency`, built the same day and tested on fakes. The
API answers at `api.business.govt.nz/gateway/insolvency-trustee-services` (v5), the key in the `Ocp-Apim-Subscription-Key`
header, read from the credential folder (support's loader pattern).

1. **Is the page open?** The public search (`app.insolvency.govt.nz/ui/public/search/insolvency-register`) is free, needs no
   login, and searches one name or one insolvency number at a time; a logged-in view adds detail only for a debtor or creditor
   of the estate. The Insolvency Register API (`portal.api.business.govt.nz/api/insolvency-register`) serves "authorised users":
   a subscription to its product on the MBIE API portal, which "our API support team may request further information before
   the subscription can be approved". It searches by estate number, name, NZBN or a date range. The estate holds an NZBN API
   key on that portal; that key's product is not this one. No challenge was met on either host.
2. **Is storing it lawful copying?** The API's own page sets the terms of holding a copy: the publisher recommends asking on
   demand rather than keeping a database; one who keeps a copy "must use the GET /insolvencies/removalorcorrections operation on
   at least a daily basis" and remove what it returns at once (discharged, completed or suppressed estates, and suppressed or
   corrected addresses), and the onus of the Privacy Act 2020 and the insolvency legislation is the holder's.
3. **What terms did we accept?** The API product's, by subscribing in the estate's name on Arthur's word (2 November 2026):
   the removals asked at least daily and applied at once, the display windows below, suppressed estates and addresses out.
4. **What does privacy law, or the statute, limit?** The Insolvency Act 2006's register rules as the API page states them: a
   record is used or shown for at most four years from discharge from bankruptcy or from a no asset procedure, and five years
   from a debt repayment order, except a person bankrupt two or more times, or bankrupt and discharged from a no asset
   procedure; suppressed estates and addresses are removed at once. A person's address is never published (hard limit 15).

How the lane runs (`registers/insolvency/spec.md`): the date-range search daily for new and changed estates, the removals-and-corrections
call daily with each removal applied the same day, each answer landed by hash, the retention windows above as a rule in the
publish, never an address. The addresses and the month and year of birth are held (3 November 2026) only in the capture's
private ledger, never in a landed document or a published view, and an estate's are deleted the day the removals name it. Searching the public search page in bulk, or calling the search page's own back end in place of the
API, would get around the subscription, and is not done.

Floor: 5 s between requests, one at a time, off-peak.
