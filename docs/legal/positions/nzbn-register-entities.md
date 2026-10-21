# The NZBN register's entity detail (incorporated societies; widened 21 October 2026 to every entity kind a product asks about or watches)

hosts: api.business.govt.nz

Draft, written by the societies session on 20 October 2026 under ruling 61
(a position is written before product, not before capture). The integrator
moves it to `docs/legal/positions/` at the merge; until then the lane's
capture passes this folder to the fetch gate. A lawyer reviews it before
anything is sold.

Class: the NZBN register's per-entity detail for an incorporated society
(NZBN Act 2016; Incorporated Societies Act 2022), one request per society:
`GET https://api.business.govt.nz/gateway/nzbn/v5/entities/{nzbn}`, with our
own subscription key. Lane: `registers/societies`. This position covers that
path only; no search listing is crawled, the society list comes from the
Companies Office's monthly file.

1. **Is the page open?** Yes, through a key issued to us. MBIE's portal
   issues a free subscription key to anyone who registers; the key in
   `~/.querynz/nzbn.env` is Arthur's own (proven live 15 September 2026). No
   lock is got past, no login that is not ours is used, no challenge is
   solved. Private primary business data needs the entity's own authority
   (three-legged OAuth); we never ask for it.
2. **Is storing it lawful copying?** The portal says "There is no fee for
   using this API" and names no licence; it points to its copyright page.
   The Companies Office's copyright page licenses its material under CC BY
   4.0 but excludes "the public notices and contents of the registers". So
   the register's contents are public by statute (the NZBN register and the
   societies register are public registers), copied for search and citation,
   attributed to the register, with the bytes kept as evidence of what it
   said on a day. The lawyer is asked whether that copying is permitted
   (open question, carded).
3. **What terms did we accept?** Those of the portal at registration
   (`portal.api.business.govt.nz`; copyright and privacy pages
   `api.business.govt.nz/copyright`, `/privacy`). The API page states no rate
   limit. It asks that batch jobs avoid the weekly maintenance window,
   Wednesday 21:00 to 23:00, and recommends `ETag` with `If-None-Match` so an
   unchanged entity answers 304 with no body. We keep off the window; the
   fetch gate does not yet return response headers, so `ETag` waits on the
   gate (card) and each society is asked once a week meanwhile. The exact terms
   text accepted at registration is to be read and kept beside this page
   (card).
4. **What do privacy law and the statute limit?** Officers' names, roles and
   dates are on the public register. An officer's residential address is not
   shown by the register and is never shown by us (hard limit 15): any
   address an answer carries goes to `societies_private` and nowhere else.
   A name the register suppresses is suppressed on every surface (hard
   limit 16). Privacy Act 2020, principles 8 and 11: rows are kept as the
   register stated them, with the date read, and a role's end is the
   register's own.

**Politeness.** One request per society, a seventh of the registered
societies a night (about 3,300), party societies first; serial; at least 5 s apart (the lane's
own floor until the integrator sets one in the gate's `FLOORS`), or a stated
crawl delay if slower; 01:00 to 06:00 NZDT, never
Wednesday 21:00 to 23:00; `If-None-Match` once the gate returns headers. A
403, 429, 5xx or challenge stops the night's run for the host.

## Widened to every entity kind (companies-2, 21 October 2026)

The companies lane's monitor (step 5.5, `registers/companies/monitor.py`)
asks the same path, with the same key, for any entity a product asks about
or watches: companies, sole traders, partnerships, trading trusts and
societies. The four answers, read 21 October 2026 and recorded in
`docs/status/companies.md`:

1. **Open?** Yes, with our own free subscription key; no lock got past.
2. **Lawful copying?** The register is public by statute (NZBN Act 2016,
   Companies Act 1993). The portal names no licence ("There is no fee for
   using this API"; "MBIE is not liable for the accuracy"). Copying register
   contents is the lawyer's question, carded
   (`the-nzbn-api-terms-and-the-copying-of-register-contents`).
3. **Terms accepted?** The portal's at registration; no rate limit stated
   anywhere read (portal page, nzbn.govt.nz terms of use). Asked: keep batch
   jobs off Wednesday 21:00 to 23:00; use `ETag`. Ours: at most 300 calls a
   New Zealand day, serial, at least 5 s apart, 22:00 to 01:00 NZ time
   (before the societies lane's 01:00 asks of the same host), never
   Wednesday 21:00 to 23:00; a 403, 429, 5xx or challenge stops the night.
4. **Privacy and statute?** Directors' and shareholders' addresses are
   persons' and go to `companies_private` only; so does every address of a
   sole trader, partnership or trust; e-mail and phone are never read. Only a
   company's or society's registered office is shown (hard limit 15). A name
   the register withholds (a sole trader's) stays withheld; a suppressed name
   is suppressed on every surface (hard limit 16).

Profile `nzbn-entity-detail-any-kind` (version 1) names what is read from an
answer; job `qv4-companies-monitor` runs it nightly at 23:30 NZDT.
