# Identity and Connections: Risk Register

Oct 10, 2026 · @arthur falls

## How to read this

This lists the ways connecting registers through identity can produce a false link, with a proposed guard for each. It records a discussion on 10 October 2026. Nothing here is ruled and nothing is measured.

Each row carries a source tag:

- **Record**: QueryNZ has already paid for this failure, and the incident is in the project's own documents.
- **Practice**: a standard failure in record linkage, the field of matching people across databases.
- **Proposal**: a judgment made in the discussion, not yet tested against the data.

Four terms are used throughout:

- **Sighting**: one register row that names a person or company, with whatever else that row carries (address, business number, date, role).
- **Arm**: one rule allowed to say two sightings are the same person. Two are ruled (ruling 221): the same first, middle and last name; or the same first and last name at the same street address.
- **Carried match**: a pair an arm has declared the same, firmly enough that the system acts on it.
- **Candidate**: a pair that looks alike but no arm held. It is shown as a possible namesake and nothing acts on it.

## Wrong identity

Seven ways two different people or companies get treated as one.

| Risk | How it creates a false link | Proposed guard | Source |
| --- | --- | --- | --- |
| Common full names | The full-name arm assumes first, middle and last is unique. Against 1.19 million director rows it is not, and fathers and sons often share all three. | Measure repeats by name-frequency band. The arm carries only in bands that pass; a common name needs a second piece of evidence. | Practice |
| Shared addresses | Accountants' and lawyers' offices, registered-office services, family homes, and apartment blocks where the unit number is dropped. | Keep the hub floor (ruling 217). Keep unit numbers in the address key. Flag service addresses apart from residential ones. | Record, Practice |
| Misread names | Most donor rows come from documents read by OCR. A name one character off can match a different real person. | A name from one unconfirmed reading cannot carry identity. This is the same question as the row-basis ruling already asked (run sheet §AS). | Record |
| Chaining | A matches B on name, B matches C on address, so A becomes C. One wrong link merges two networks. "New Zealand Government" once absorbed 444 entities this way. | No automatic chaining. A cluster forms only when every pair in it is consistent. Oversized clusters are held for review. | Record |
| Company names | Where a source gives only a name, the business number is guessed. Names are reused after removal, and near-identical names exist (Tower Limited and Tower Corp Holdings). | Join on the business number where the source gives one. A name-only join needs an exact name and a company that existed on the date of the event; otherwise abstain. | Record |
| Name-key defects | Macrons, hyphens and apostrophes handled differently in different places. Past losses fell on Māori, Pasifika and Irish names. | One name-key function, with a test that refuses a second. The answer key includes these names on purpose. | Record |
| Hand merges | A curated merge is a person's judgment. It can be wrong and it stays until someone looks again. | Each hand merge records its evidence, date and ruling, and the fold watch (ruling 220) revisits it. | Record |

## Right identity, false connection

Seven ways a correct match still produces a misleading link.

| Risk | How it creates a false link | Proposed guard | Source |
| --- | --- | --- | --- |
| Time | A director in 2010 linked to a contract in 2024. Several registers are thin on dates: MP end dates default to term boundaries, and the roster once showed 137 sitting MPs against 123 seats. | Every hop carries a from and to date. A chain holds only where the dates overlap or follow in the stated order. An undated hop is shown as undated, never assumed current. | Record |
| Hubs | Professional directors, nominee shareholders, large accounting firms and the Crown connect everyone to everyone within three hops. | Cap how many links a node may have before chains through it are excluded or flagged. Limit the number of hops. | Practice |
| Role meaning | A nominee holding shares on trust is not an owner. The August role check found 22 beneficiaries recorded as trustees. | One role vocabulary per register. A list of nominee and professional holders. Each link is labelled with the role as filed. | Record |
| Parent and subsidiary | A donation by one company and a contract to its parent are related, but not the same party. | Ownership stays an annotation and is never shown as the same party (ruling 253). | Record |
| Coincidence shown as cause | Wealthy businesspeople both donate and sit on boards. A correct chain can imply something untrue. | Descriptive wording only. Show the base rate beside the chain: how many donors of that size hold any appointment at all. | Proposal |
| Double counting | The same gift on a return and a disclosure, joint donors, amended filings. | Already ruled (193, 277, 357): the return is the record, a joint row is counted once, amendments supersede. Any new join must pass through the same rules. | Record |
| Absence read as "no connection" | A blank where a register is not held, or only partly held, reads as a clean result. | State coverage wherever a blank is shown. "Not held" and "none found" are different answers. | Record |

## Weak points in the approach itself

Eight places where the method, not the data, could let a false link through.

| Risk | Why it matters | Proposed guard | Source |
| --- | --- | --- | --- |
| The answer key is too easy | MPs are well documented and carry Parliament's own id. Donors and directors have commoner names and less evidence. A key built mostly from MPs flatters every arm. | Weight the key toward donors and directors. Include known namesakes as "different" pairs. About 200 pairs minimum; the merge refuter stalled on 13. | Proposal, Record |
| One averaged error rate | At 1 wrong in 100 over a million rows, thousands of folds are wrong, and they cluster in common names. | Report error by name-frequency band and refuse an arm in the bands where it fails. | Proposal |
| Unstable row ids | The nightly derive renumbers rows. The same fault once left 1.1 million citations pointing at nothing. | A sighting id built from the document and the row's position or content, so it survives a rebuild. A test that a rebuild keeps every id. | Record |
| Judgments tied to a weights version | Any change to the scoring reopens the 127 identity cards already cleared. | Key each judgment to its arm and its evidence, not to a global version. | Record |
| Review verdicts outside the system | Identity verdicts sit in a file outside the repository, and 96 of them were read by nothing downstream. | The verdict ledger becomes a store the service reads and the backup covers. A rejection is a standing refusal. | Record |
| Address evidence disappears | Director addresses start being suppressed on 18 November 2026, and address is one of the two arms. | Seal the pre-redaction copy before that date (card C232). Addresses are used for matching and never served. | Record |
| Privacy | Joining registers builds a profile of private people. A wrong link about someone who is not a public figure is real harm. | Legal advice before person-to-person connections are published (backstop 1 November). The suppression list applies to connections. Start with people already in public roles. | Proposal, Record |
| The check beside the question | The project's most repeated failure is a check that measures the thing next to what matters and reads green. | Every identity gate is shown to fail on a planted wrong match before it is trusted. | Record |

## Guards that cut across the whole list

Seven rules apply to every risk above.

- **Abstain by default.** A pair is carried, shown as a candidate, or left alone. No arm, no match.
- **Every match is reversible and shows its basis.** The registers stay as filed; a match is a judgment in a ledger, and withdrawing it regenerates the view.
- **The answer key runs on every derive.** It is the standing check, not a one-off test.
- **Counts reconcile.** Sightings in equals carried plus candidate plus abstained, on every run.
- **Clusters are checked for contradiction.** Two rows in one identity with different middle names or impossible dates hold the whole cluster.
- **One name key and one address key.** Each has a test that refuses a second.
- **Corrections feed the key.** Anyone who writes in to say "that is not me" becomes a confirmed wrong match.

Arthur reviews rules and samples, never individual matches.

## First measurements

Six cheap counts would turn the proposals above into findings. None has been run.

1. **Repeated full names.** How many first, middle and last names appear on more than one director identity, by name-frequency band.
2. **Address hubs.** How many distinct names share each address, and how many existing folds rest on a busy one.
3. **Error rate of the two ruled arms.** A random sample of 100 existing carried matches, both sides read against the documents.
4. **How often an arm can fire.** Per register, the share of rows that carry a middle name or an address at all. This sizes the abstain pile.
5. **Company names to business numbers.** The share of donor company names that match exactly one company live on the donation date.
6. **Cluster shape.** The size distribution of identities, and any that already hold conflicting middle names.

## Rulings owed

Six decisions are Arthur's.

- [ ] The error bar: what share of carried matches may be wrong before an arm is refused. Suggested starting point is 1 in 100, judged per name-frequency band.
- [ ] Whether any third arm is measured for admission, such as the same name tied to the same company in two registers.
- [ ] Whether person-to-person connections are published before the legal advice is in hand.
- [ ] Whether the terminal architecture is amended: people as first-class, a connections layer, and the product line.
- [ ] Whether the press graph goes into maintenance (pencilled in on 10 October).
- [ ] The row-basis tier for a name from one fresh reading (already asked, run sheet §AS).

This page lives outside the repository. For any of it to bind the work, the working session needs to card it.
