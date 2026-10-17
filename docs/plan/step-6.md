## Step 6: register scans

**Goal.** The scan shape and four templates on it. A scan asks one question of every row, such as "which suppliers share a director with a donor?", and lists the answers with their citations.

**Why after step 5.** A scan needs the groups built for every person, and the two trust settings. Both settings have defaults (see "3. Links"), so this step does not wait for a ruling. Put the measurements from step 4 and your recommendation to Arthur in the decision queue before this step starts; if he has not ruled, build on the defaults and keep them as settings.

**Models.** Fable for the shape and the multi-step rule. Opus for lanes and templates.

### Do

**6.1 Build the scan shape.** A scan is a saved question, the registers it reads, the trust rule it applies to chains, and a list out. Every line in the list carries its citations and its grade. A scan re-runs when its registers change.

**6.2 Templates, in this order.** Each ends with a checkpoint.

| Order | Use case | Runs on | Note |
| --- | --- | --- | --- |
| 1 | 10 Tender and award intelligence | 29,874 award notices from 2014, keyed on official business number, held and never read | Needs a reader and a scheduled refresh; the file is refreshed by hand each quarter today |
| 2 | 9 Government procurement integrity | Awards joined to directors, shareholders and donors | A donor-to-award join is the plainest case of coincidence shown as cause. It stays off the public site unless Arthur decides otherwise |
| 3 | 14 Post-settlement governance map | Charity officers, Māori business identifiers, company roles | Needs the iwi and hapū directory and the settlement commitments database, both public. The Māori Land Court needs registration. 200 Waitangi Tribunal reports are held under an old ruling that asks for a named use case: put it to Arthur |
| 4 | 15 Lobbying | Gazette appointments, MPs' interests, the Hansard register, ministers' diaries | Arthur, 17 October: four products in order — (a) the ministers' diary register (a built register from the monthly proactive-release PDFs; no dependency, so it can go into the registers milestone early); (b) who each minister met and what those people and organisations represent, resolved against the spine, so after links (and the first real job for track D.2); (c) the legislation join — minister ↔ portfolio ↔ bill ↔ Hansard speech, with the meetings beside it by date, and an "articles mentioning" section that retrieves and asserts nothing; (d) discourse, which is its own product, use case 17. Ministers only: backbench MPs publish no diary. The template will still say "not held" often |

**6.3 Sources this step adds.** All public.

- Live open tenders, agency contract disclosures, council procurement on other platforms.
- Grants: gaming-machine societies, Lottery, regional development funding, tertiary funding.
- Council minutes from 24 councils on one meeting platform are held with no read of attendance or resolutions.
- Local election returns and councillors' interests, council by council.

**6.4 A question for Arthur, not blocking.** Whether the award join, pre-2019 awards or a councils tier ever appear on the public Follow the Money site. The capability is built either way.

### Done when

- [ ] The two trust settings are ruled, or their defaults are recorded as in force.
- [ ] The award notices are read, refreshed on a schedule, and checked against the source's own count.
- [ ] Each of the four templates has had its checkpoint and has a known-limits page.

### Brief to paste

```text
You are a build session for QueryNZV4 on node2, running as the model
docs/briefs/next.md names, in the working copy the launcher made for
you. Read docs/PLAN.md, then docs/status.md, and continue where it
stops. Do the part of step 6 named here: <the scan shape, in
products/scan/ | the template for use case N, in its folder under
products/templates/ | the lane for <source>, in registers/<lane>/>.
A scan lists what the registers show with dates and citations; it
never says one fact caused another. Nothing from this step goes on
the public site. Run the checkpoint when a template is built. Push
your branch and raise a merge request. Finish by telling Arthur what
closed and what is carded.
```

