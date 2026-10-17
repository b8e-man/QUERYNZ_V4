## What we are building

An estate of New Zealand public records that does five things: it **copies** public registers, **builds** registers where none exists, **links** rows across them, **answers** questions from them with a citation, and **checks** itself. Everything else is support.

This is a capability build-out. Plan and build as if customers exist for every use case. Billing, accounts and metering are out. The first product is Follow the Money, rebuilt on the new estate and compared with the frozen site.

**The core architectural change** (Arthur, 16 October): a rich spine made of multiple joined registers. Everything above — the links, the products, the board — is a view of that spine, and the spine is what later work resolves against. See "Notes from Arthur, 16 October 2026" in the reference section.

### 1 and 2. Registers: copied and built

| Kind | What it is | Examples |
| --- | --- | --- |
| Copied | Someone else's register, held as a copy and kept fresh | Companies with directors and shareholders; charities and officers; tender awards; the Register of Political Parties; LINZ title owners and place names; MPs' declared interests |
| Built | A register that exists nowhere, assembled from notices or filed documents | Insolvency appointments, director prohibitions and public appointments from the Gazette; donations and party returns from Electoral Commission filings; regulator actions; court judgments |

Rules every register follows:

1. **The captured document is kept unchanged.** It is the only thing that cannot be rebuilt.
2. **Every row is rebuilt from its documents.** A wrong row is fixed by fixing the reading or adding a correction, never by editing the row.
3. **Every row has a stable key,** the same across re-reads, amendments and nightly rebuilds. For a copied register the key is the source's own identifier for that row (a company number with a role identifier, a charity number with an officer identifier), so it survives each new monthly file. For a built register it is the document's hash with the page and the place on the page; an amended filing is a new document whose rows point back to the rows they replace. A key never depends on a row number or a file name, because both change.
4. **Every row cites its document:** the file's hash (a fingerprint of its bytes), the page, and the place on the page.
5. **Each register has one owner in the code:** one lane, one set of tables, one test set. No two lanes land through a shared wipe-and-reload.
6. **A reading that fails its own check publishes nothing,** not a number.
7. **Every lane has one figure checked against the outside world,** such as the source's own total.
8. **Nothing is set aside silently.** Every lane keeps a catch log, and items in must equal items out plus items set aside.
9. **A register goes back as far as its source does.** The 2019 window belongs to the Follow the Money template alone; no lane inherits it.

**Rule 10, added by ruling 54: a register rebuilds in parts.** One document, or one day's file from the source, can be read again and its rows replaced without rebuilding the rest, and one register rebuilds without touching another. A lane's wipe and reload is the full path and this is the quick one. The same holds downstream: links, groups and search tables are recomputed for the keys that changed. The check that the quick path and the full path agree is a rolling one: each night the next register in turn is rebuilt whole into a staging schema, compared and dropped. The Papers Past archive is checked on a sample of items and never rebuilt whole. The old estate's answer set took 40 to 90 minutes to rebuild after any change.

### 3. Links

There is no stored person. There are three tables, and a person is what you get by reading them together.

| Table | What it holds | Who writes it |
| --- | --- | --- |
| Links | A pair of rows that join, the rule that joined them, the evidence, and a grade: confirmed or near | The joining rules, on every rebuild |
| Decisions | A remembered ruling on a pair, one of three: "the same", "not the same", or "contested" (the link drops to near). Each records who or what made it and on what evidence. Only ever added to | The review agent, corrections, suppressions; the old estate's judgments, copied across |
| Groups | Rows gathered into people by following confirmed links, minus the decisions. Rebuilt whenever either table changes; never edited | Nobody: it is computed |

Organisations need none of this where a register gives them an official number. The number is the link.

**How a link is made**

- **One shared reading of names and addresses.** "J. A. Smith", "John Adam SMITH" and "Smith, John" come out the same everywhere, and so do addresses. One function, imported, never copied. Macrons are kept.
- **Two rules confirm a link between person rows** (old ruling 221): the same first, middle and last name; or the same first and last name at the same street address.
- **A busy address needs a middle name:** an address shared by more than 50 companies counts only when the full name carries a middle name (old ruling 217). Address alone never confirms.
- **Everything else makes a near link,** shown as a possible namesake with the reason it is only near.
- **Joining a politician to a company role is stricter.** An MP's or candidate's name found on the director register counts only with a supporting link, whatever the name similarity: a shared directorship, a shareholding, or a company that person declared. Of 151 name-matched MP directorships in the old estate, 15 had one. The rest are kept and labelled as namesakes.
- **A joint filed name is one donor. A parent and its subsidiary are a group, not one party.**
- **These rules are exact for Follow the Money.** For the wider estate they are the starting point, revisited only after the first measurements and only by Arthur's ruling.

**How a link is unmade**

- **Every confirmed link is watched** for signs it covers two people: appointments in different regions at once, a very common full name, a bankruptcy on one row while the other keeps appointing, donor rows from far-apart addresses in one year.
- **A review agent reads the evidence and splits the link if it cannot trust it.** Splitting is the safe direction.
- **A split is a decision added, then a rebuild.** Nothing is deleted and nobody edits a group by hand.

**Two settings are ruled from measurement, and each has a default until then.** Build both as settings, not as code.

- **How far a chain of links is trusted** (A joins B, B joins C). Default: a group follows chains of confirmed links, as the old folds did, and any group the watch flags is contested as a whole. Follow the Money needs this default to reproduce the frozen site.
- **How much doubt each step through a person adds** to a multi-step connection. Default: a connection that passes through more than one person is listed as near, never confirmed.

### 4. Products: four shapes

The sixteen use cases sit on four shapes. A shape is built once; a use case is a template on it. A fifth shape, the board, serves no single use case.

| Shape | What it does | Use cases |
| --- | --- | --- |
| Published site | Publishes totals and pages from a fixed set of registers, on a schedule | 1 Follow the Money |
| Subject report | Starts from one person or organisation and reports what the registers hold: confirmed connections, then near connections | 2 Legal counterparty and conflict check; 3 Banking director history; 4 Agriculture counterparty; 5 Business credit and monitoring; 6 Insurance underwriting; 7 Construction and phoenix detection; 8 Recruitment board screen; 11 Healthcare operator governance; 12 Property developer due diligence; 13 Beneficial ownership and AML |
| Register scan | Asks one question of every row and lists the answers | 9 Government procurement integrity; 10 Tender and award intelligence; 14 Post-settlement governance map; 15 Lobbying |
| Archive search | Finds documents by keyword, by meaning, and by the names in them | 16 History search over Papers Past; keyword search over other journalism; 17 Discourse (the press graph's return, scoped: who said what about a subject, aimed at whom) |
| The board | One search across every register, shown as a row of panes that grows to the right as each link is followed | None of its own. It is the way to look at the estate itself (ruling 52; step 4.9) |

A template holds five things:

- **Which published tables it reads.** This is also all it is allowed to read. Each is listed with its licence terms, any attribution it requires, and how often it must be refreshed.
- **Its sections,** in order. A template may include a section headed "articles mentioning", fed by keyword search over journalism. It retrieves; it asserts nothing.
- **Its own rules:** warning flags, and patterns such as a failed company restarted under a new name.
- **Its known-limits page:** what the product cannot see, stated to the reader.
- **Its owner and version.**

Monitoring is a subject report run again when one of its registers changes.

Rules for every product:

1. **A product reads only the published tables its template names.** Never the inside of a lane.
2. **A product never writes into the estate.** It writes its own state only. When a product wants a record refreshed, it raises a request and the lane that owns the record does the work.
3. **Export is tested, not assumed.** A use case is exported as its shape, its template and a copy of the tables it reads. Build the bundle, start it with no connection to the estate, and run its checks.
4. **Withdrawals reach every copy:** a suppressed name within 24 hours, a correction within 5 working days, and the director-address seal. So an export needs either a refresh channel back to the estate or a recorded handover of those duties.
5. **Licences travel with the data.** Award notices need attribution. Land title data on individuals may not be publicly indexed.
6. **No second copy of logic.** If a product needs a result the estate computes, it gets the result as a column, not a copy of the function.
7. **Every product's surface is a web app on its own port, reachable on the local network only.**

Rules for everything a product shows:

- Every figure links to the document it came from.
- A blank says whether it means "none found" or "not held".
- A total states what it leaves out.
- An unreadable name is shown as unreadable, never hidden, guessed or ranked.
- A figure read from pixels is weaker evidence than one read from a text layer, and is marked as such.

### The Follow the Money template's own settings

These bind that one template and nothing else. They are what make the rebuilt site match the frozen one, so none of them moves. **They are as the frozen site stands at the freeze tag, not as this plan was first written:** the old repository moved after `2d3874e` (the race definition, ruling 361; the party page's selector; the published search's aliases), and the baseline of step 1.3 records the tag. Where this list and the frozen site differ, the frozen site wins.

**Scope**

- Calendar 2017 onward, whole (ruling 364, 17 October): every figure from 1 January 2017; **2017 is not a race (ruling 366, the same night)** — the races are 2020, 2023 and 2026, and 2017 to polling day is in the whole-window figures only; (364's text, superseded on this point: the 2017 election is a race of its own, and 23 September 2017 splits 2017's named rows between the 2017 and 2020 races by each donation's own date (ruling 363). Earlier rows are kept and never published; every Part A line's date is read.
- Seven front-page parties: National, ACT, Labour, Green, NZ First, Te Pāti Māori, Opportunity. Other parties' data is kept and served, not worked.
- A renamed party is the same party.
- A race is every calendar year after the election before it, up to and including its own (ruling 361, 16 October), inside the window: 2020 is 2018–2020 for return totals and from 24 September 2017 (the day after the 2017 election) for named donors (ruling 363); 2023 is 2021–2023; 2026 is 2024–2026. 2017 is not a race (ruling 366): 2017 to polling day is in the whole-window figures only. Every figure the selector governs is cut by it: the card figures, the party page's figures, donor roster, broadcasting allocation and size map, and the home page's four bars, the electorate map, list and totals.
- No press-reported row.

**Money**

- A donation is from the donor the Commission filed it under. A wholly-owned company keeps its own row; ownership is a note and is never added to the owner's total.
- If a return covers the money, the return is the record. A separate large-donation disclosure of the same gift is never added.
- The headline is all donations: the return's declared total. Named donors come second.
- One figure per party-year, with its basis named. A party's own committees and branches are not outside donors.
- Where our reading and the Commission's figure differ, the Commission's is the headline, linked to the Commission's own page.

### 5. Checking

Without checks a wrong answer looks the same as a right one.

| What is checked | How |
| --- | --- |
| A register | Row counts against the source's own totals; sums against official figures where they exist; freshness; every row has a citation |
| A reading | The catch log. Each document that could not be read is named, with the stage it stopped at |
| The links | Error rate measured by how common the name is, on test pairs the registers themselves supply |
| The review agent | Scored on those same test pairs before it may split anything on its own |
| A product | Tested when built. What fails becomes a card and a line on its known-limits page |
| Follow the Money | Compared figure by figure with the frozen site. Every difference is explained by a card |

### How the code is laid out

Three kinds of module, with imports running one way, held by one test.

| Folder | Holds | May import |
| --- | --- | --- |
| `keys/` | The one reading of names, addresses and official numbers. Pure functions, no database | Nothing |
| `support/` | The scheduler, the document reader, the model client, the fetch gate, the landing wrapper, the document profiles, the release pipeline, the installer | `keys` |
| `registers/<lane>/` | One lane each: capture, reading, its tables, its outside check, its catch log, its short spec | `keys`, `support` |
| `links/` | The joining rules, the three tables, the watch, the review agent | `keys`, `support`, published register tables |
| `products/<shape>/` and `products/templates/` | The four shapes and one template per use case | `support`, published tables |
| `checks/` | The checks board and the comparison with the frozen site | `support`, published tables |
| `cards/`, `lessons/`, `docs/` | One file per card and per lesson; the plan, the decisions, the status file | Not code |

**A published table** is a view in a schema named `pub`, owned by the lane or by `links`. It is the only thing a later module may read. A test in the merge gate fails if any module imports from, or queries, the inside of another.

### Deliberately not built

- The press graph as it was: people and claims drawn from journalism at large. Parked. It returns SCOPED, as use case 17 Discourse (Arthur, 17 October) — one subject at a time, after links, with the joined registers as what its names resolve against (Arthur, 16 October: once the registers are joined, "we can use them for name resolution for press"). Until step 4 is closed nothing resolves a press name.
- A stored person record, or any graph database.
- Billing, accounts, metering.
- Anything from NZME or fyi.org.nz.
- The later list: mayoral diaries, chief executives' gifts and expenses. (Ministers' diaries came off it on 17 October — use case 15.)

