## Step 5: subject reports, legal documents and company monitoring

**Goal.** The subject-report shape, ten templates on it from easiest to hardest, the legal sources read in, and company records kept as fresh as the official interface allows.

**Why this order.** Ten of the sixteen use cases are subject reports, and four of them run on data already held.

**Models.** Fable for the shape, the legal-document research and the monitoring design. Opus for lanes and templates.

### Do

**5.1 Build the subject-report shape.** One builder:

- It starts from one row, a person or an organisation, chosen by the user.
- It walks confirmed links outward and lists near links beside them, each with its reason.
- It fills the template's sections from the registers the template names.
- It applies the template's own rules and flags.
- Every statement carries its citation. Every blank says "none found" or "not held".
- It can print as a memo.

Harvest from the old estate, as ideas and tests more than code: the August flows for Legal, Banking, Recruitment and Agriculture; the report builder and printable memo; the seven-rule person set and the four-rule company set in `data-layer/flags`; the ownership-chain page; the checklists in `data-layer/docs/USE_CASE_REQUIREMENTS.md`. They were built on the old graph.

Presentation rules for every report, because these are the ways a true link misleads:

- **Every connection is dated.** An undated hop is marked as undated.
- **Hubs are flagged:** professional directors, nominees, the Crown, an address with a thousand companies.
- **A nominee is not an owner.** A role is shown as the register states it.
- **Coincidence is not shown as cause.** Two facts sit side by side with their dates; the report does not join them with "because".
- **Absence is not a finding.** "No connection found in the registers held" is the most a report can say.

**5.2 Templates, in this order.** Each ends with a checkpoint.

| Order | Use case | Runs on | Waits on |
| --- | --- | --- | --- |
| 1 | 8 Recruitment board screen | Held data | Nothing |
| 2 | 4 Agriculture counterparty | Held data | Nothing |
| 3 | 3 Banking director history | Held data | The securities register for the full picture |
| 4 | 2 Legal counterparty and conflict check | Held data | Court judgments, from 5.4 |
| 5 | 13 Beneficial ownership and AML, domestic half | Ownership chains through held shareholdings | Sanctions lists, limited partnerships, overseas data |
| 6 | 7 Construction and phoenix detection | The insolvency file, disqualified directors, the change history | The building practitioners register |
| 7 | 5 Business credit and monitoring | Monthly grain at first | 5.5 for freshness; the insolvency and securities interfaces |
| 8 | 6 Insurance underwriting | WorkSafe releases, regulator actions | Courts and tribunals |
| 9 | 11 Healthcare operator governance | Retirement villages file, charity returns | Health and Disability Commissioner decisions |
| 10 | 12 Property developer due diligence | Company side of land titles, overseas investment decisions | Building consents, courts |

The templates for use cases 2, 6, 11 and 12 gain an "articles mentioning" section once the journalism keyword search of step 7.6 exists. Template folders are `products/templates/<number>-<short-name>/`, for example `products/templates/08-recruitment/`.

**5.3 Lanes this step adds.** Read what is already held before acquiring anything.

| Held and unread | What it gives | Note |
| --- | --- | --- |
| The company insolvency file | Insolvency type, appointees, dates | Read today only as background |
| Change history, 16 tables | Trading names, industry and roles as they change | Kept only since 16 August 2026 |
| Commerce Commission cases and FMA warnings | 112 cases and 16 warnings, parties parsed | The Act section is empty on all 128 |
| Disqualified directors | A derive already written | Its three tables have no definition anywhere |
| Charity annual returns | 421,633 returns | No typed read |
| Retirement villages file | Statutory supervisor name and date | Contents need a look |
| WorkSafe releases | Release texts | A read of prosecution facts from the text |
| Overseas investment decision summaries | Applicant, vendor, price | No read |
| Land titles | Company owners matched | Individuals are held back under the licence. The licence obliges amending or deleting on request, so the takedown service is built before any individual's row is used |

| To acquire, all free and public | For |
| --- | --- |
| Sanctions lists: Foreign Affairs, United Nations, Police designations | 13 |
| Limited partnerships register | 13 |
| Licensed building practitioners | 6, 7, 12 |
| Health and Disability Commissioner decisions | 11 |

Waiting on outside approval since 19 September, and not to be worked around: the securities register, the Insolvency Register and the financial service providers interfaces. The insolvency interface brings a daily removals check for good. Until they arrive, the templates that want them say "not held".

**5.4 The legal documents.** Arthur's ruling 18: these sources are in. They were held because they need good profiles and good reading, not because they were unwanted. Easiest first.

1. **The parsed case-law interface (OpenLaw).** The key is in hand and tested; about 47,000 cases, already parsed, so no page reading. Build the lane.
2. **The court judgments already captured.** The courts register exists in `data-layer/courts_register` (parse, derive, suppress) and is fed by nothing; 145 documents were in scope. A consolidated appeal names several parties in one line: emit one row per party and role. Repoint its suppress lever, which defaults to the old graph.
3. **Research how legal documents are structured,** and write it up before building further: neutral citations, parties, outcomes, numbered paragraphs. An earlier pipeline kept evidence by numbered paragraph; port the idea, do not resurrect the code. Write a profile per court format.
4. **Repeat the page-reader trial on scanned legal documents.** The September and step 3 results cover electoral returns only.
5. **Tribunals, employment and environment courts, coroners.** They were paused on a robots signal, which no longer decides anything. Apply the capture test and write the one-page position. A permission letter to the Ministry of Justice is drafted and unsent; sending it is Arthur's. Capture of an open page does not wait for the letter. It waits only where the site blocks or challenges.
6. **Not reopened:** the High Court and Court of Appeal back-catalogue, which drops automated requests; the legal-information site that requires an agreement.

**A court's suppression order binds every product.** A name a court has suppressed is suppressed on every surface.

**5.5 Company monitoring** (ruling 19).

- The monthly import stays as it is.
- **Whenever a product looks an entity up, the estate checks that entity against the official business-number interface.** The product does not do this itself, because a product never writes into the estate. It raises a request; the companies lane makes the call, lands the answer as a document, and rebuilds that entity's rows from it. The interface has no change feed, so this is the deepest it allows. It answers in about 0.6 seconds per entity; the access key is in the credentials folder and was last used in August.
- Each difference is stored as a dated change. This is what finally gives an ended role its real end date.
- Watched entities are checked on a schedule, not only on lookup.
- Sole traders, partnerships and trusts are not in the monthly file and are reachable only this way, one at a time.
- An exported copy of a product does not call the interface. It is refreshed from the estate.

### Done when

- [ ] The shape passes its tests and prints a memo.
- [ ] Each of the ten templates has had its checkpoint and has a known-limits page.
- [ ] The OpenLaw lane and the courts register are fed and checked against a figure from their source.
- [ ] The legal-document research note and its profiles exist.
- [ ] A lookup updates the register from the interface, and the change is dated.

### Briefs to paste

```text
You are a build session for QueryNZV4 on node2, running as the model
docs/briefs/next.md names, in the working copy the launcher made for
you. Read docs/PLAN.md, then docs/status.md, and continue where it
stops. Do the part of step 5 named here: <the subject-report shape,
in products/report/ | the template for use case N, in its folder
under products/templates/ | the lane for <source>, in
registers/<lane>/ | the legal-document research, in docs/research/ |
company monitoring, in registers/companies/>. A template may read
only the published tables it names. Date every connection, flag hubs,
never show coincidence as cause. Run the checkpoint when a template
is built: test it, card what fails, write the known-limits page. Push
your branch and raise a merge request. Finish by telling Arthur what
closed and what is carded.
```

