# The limited partnerships register, through the NZBN interface (draft position, ruling 61)

hosts: api.business.govt.nz

Class: the Companies Office's register of limited partnerships (Limited
Partnerships Act 2008), read one partnership at a time through the NZBN
register's entity detail, `GET /gateway/nzbn/v5/entities/{nzbn}`, with our
own key. Lane: `registers/limited_partnerships`. The host is already covered
by `nzbn-register-entities.md` (societies-1, widened by companies-2); this
page adds the partnerships' own statute and the bulk frame. Draft, held in
the lane's folder because the fence keeps a build session out of
`docs/legal/positions/`; the integrator moves it there. Read 21 October 2026
by sanctions-1.

1. **Is the page open?** Yes, with our own free subscription key (Arthur's,
   `~/.querynz/nzbn.env`, proven 15 September 2026). No lock, login that is
   not ours, or challenge: 15 partnerships answered 200 on 21 October 2026.
   The Companies Office's web register (`app.companiesoffice.govt.nz`) is
   NOT used: its robots file disallows everything (a record, not a
   permission) and our one read answered HTTP 500, a failed read that is
   not retried. `api.business.govt.nz` answers 404 for a robots file; no
   crawl delay is stated.
2. **Is storing it lawful copying?** The register is public by statute:
   the Limited Partnerships Act 2008, s 55(1): "The registers must be
   available for access and searching by members of the public at all
   times"; s 21: a person becomes a general partner when entered in the
   register as one; the NZBN Act 2016 makes the NZBN register's primary data
   public. (Text read from legislation.govt.nz, version as at 1 September
   2022, 21 October 2026.) The portal names no licence ("There is no fee for using
   this API"); the Companies Office's CC BY 4.0 grant excludes "the
   contents of the registers". Copying register contents for search and
   citation, attributed, with the bytes kept as evidence of what the
   register said on a day, is the lawyer's question already carded
   (`the-nzbn-api-terms-and-the-copying-of-register-contents`).
3. **What terms did we accept?** The portal's, at registration, as for the
   other NZBN lanes: no rate limit stated; batch jobs kept off Wednesday
   21:00 to 23:00. The exact text accepted is carded for the integrator
   (the societies lane's card); nothing read bars a weekly copy of one
   class of entity at our pace.
4. **What do privacy law and the statute limit?** General partners' names
   are public under the Act; limited partners are NOT: s 115(1), "The
   Registrar must treat limited partner information as confidential and must
   not make it available to a member of the public". They are never sought
   or read, and the interface's answers carry none. A general partner may be a person: every address the
   answer gives for a partner (postal, service, registered) goes to the
   lane's private twin and is never published (hard limit 15). Only the
   partnership's own registered office is shown, as a company's is. A name
   the register withholds (`privacySettings`) is blanked on every surface,
   the row kept (hard limit 16). E-mail, phone and website are never read.
   Privacy Act 2020, principles 8 and 11: rows are kept as the register
   stated them, with the day asked; the interface states no start or end
   date for a partner and none is made up.

Crawl delay: none stated. Floor: one call at a time, at least 5 s apart (the
gate's floor for the host), 21:00 to 22:00 NZ time, never Wednesday, before
the companies monitor (22:00) and the societies lane (01:00) on the same
host, a seventh of the 4,114 a night (at most 600 calls); a 403, 429, 5xx or
challenge stops the night. Author: sanctions-1 (Opus), 21 October 2026.
