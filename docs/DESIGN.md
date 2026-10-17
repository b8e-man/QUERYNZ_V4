# QueryNZV4 Design

Oct 11, 2026 · @arthur falls

The estate does five things: it copies public registers, builds registers where none exists, links rows across them, answers questions from them with a citation, and checks itself. Everything else is support.

## At a glance

&#91;embedded content: the five parts · documents, registers, links, products, checking\]

Read it top down. Documents are captured and kept. Registers are read out of them. Links join rows across registers. Products read the registers and the groups. Checking runs beside all three. Archive search also reads the captured documents directly.

## Registers

A register is a table of rows about people, organisations or events, where every row points to the document it came from. There are two kinds, and they follow the same rules.

| Kind | What it is | Examples |
| --- | --- | --- |
| Copied | Someone else's register, held as a copy and kept fresh | Companies and their directors and shareholders; charities and officers; tender awards; the Register of Political Parties; LINZ title owners and place names; MPs' declared interests |
| Built | A register that exists nowhere, assembled from notices or filed documents | Insolvency appointments, director prohibitions and public appointments from the Gazette; donations and party returns from Electoral Commission filings; regulator actions; court judgments |

Rules every register follows:

1. **The captured document is kept unchanged.** It is the only thing that cannot be rebuilt.
2. **Every row is rebuilt from its documents.** A wrong row is fixed by fixing the reading, never by editing the row.
3. **Every row cites its document and the place in it.** A citation never points at a row number, because row numbers change on rebuild.
4. **Each register has one owner in the code.** One reader, one set of tables, one test set.
5. **A reading that fails its own check publishes nothing.**
6. **Capture is legal and polite.** One page per source class states the legal position.

**A register also rebuilds in parts** (ruling 54, 12 October). One document, or one day's file from the source, is read again and its rows replaced without rebuilding the rest. This keeps a change quick to check: the old estate's answer set took 40 to 90 minutes to rebuild.

Organisations in most registers carry an official number. People almost never do. That difference is why the next part exists.

## Links

There is no stored person. There are three tables, and a person is what you get by reading them together.

| Table | What it holds | Who writes it |
| --- | --- | --- |
| Links | A pair of rows that join, the rule that joined them, the evidence, and a grade: confirmed or near | The joining rules, on every rebuild |
| Decisions | A remembered ruling on a pair: "not the same", or "the same". Only ever added to | The review agent, corrections, suppressions |
| Groups | Rows gathered into people by following confirmed links, minus the decisions. Rebuilt whenever either table changes; never edited | Nobody: it is computed |

Organisations need none of this where a register gives them a number. The number is the link.

How a link is made:

- **One shared reading of names and addresses.** "J. A. Smith", "John Adam SMITH" and "Smith, John" come out the same everywhere, and so do addresses.
- **Two rules confirm a link between person rows** (ruling 221): the same first, middle and last name; or the same first and last name at the same street address. A busy address needs a middle name (ruling 217).
- **Everything else makes a near link.** A matching name alone is shown as a possible namesake, with the reason it is only near.
- **A name found in another register needs a supporting link** before it counts: a shared directorship, a shareholding, a declared company.

How a link is unmade:

- **Every confirmed link is watched** for signs it covers two people: appointments in different regions at once, a bankruptcy on one row while the other keeps appointing, donor rows from far-apart addresses in one year.
- **A review agent reads the evidence and splits the link if it cannot trust it.** It may search the web, but only for evidence that two rows are different people. It never confirms from the web, because web presence favours the prominent.
- **A split is a decision added, then a rebuild.** Nothing is deleted, and Arthur is not in this loop.

Two things are set from measurement, not chosen in advance: how far a chain of links is trusted (A joins B, B joins C), and how much doubt each step through a person adds to a multi-step connection.

## Products

The sixteen use cases sit on four shapes. A shape is built once; a use case is a template on it.

| Shape | What it does | Use cases |
| --- | --- | --- |
| Published site | Publishes totals and pages from a fixed set of registers, on a schedule | Follow the Money |
| Subject report | Starts from one person or organisation and reports what the registers hold about it: confirmed connections, then near connections | Legal counterparty, banking director history, agriculture counterparty, business credit and monitoring, insurance underwriting, construction and phoenix, recruitment board screen, healthcare operators, property developers, beneficial ownership |
| Register scan | Asks one question of every row and lists the answers | Procurement integrity, tender and award intelligence, post-settlement governance map, lobbying |
| Archive search | Finds documents by keyword, by meaning, and by the names in them | History search over Papers Past; keyword search over other journalism |

**Added 12 October: a fifth shape, the board.** It serves no single use case. It is one search across every register, with each followed link opening a pane to the right, so the row of panes is the connection. It reads published tables, links and groups only, and creates nothing. The build plan sets it out as step 4.9.

A template holds four things:

- **Which registers it reads.** This is also what it is allowed to read.
- **Its sections,** in order.
- **Its own rules:** warning flags, and patterns such as a failed company restarted under a new name.
- **Its known-limits page:** what the product cannot see, stated to the reader.

Monitoring is not a fifth shape. It is a subject report run again when one of its registers changes.

Exporting a use case means exporting its shape, its template and the register tables it reads. Follow the Money already works this way: the published site is exported, the machinery is not.

Rules for everything a product shows:

- Every figure links to the document it came from.
- A blank says whether it means "none found" or "not held".
- A total states what it leaves out.
- An unreadable name is shown as unreadable.
- A suppressed name is suppressed everywhere; the row and the money stay.
- A company's registered address is shown. A person's home address is never shown or extractable.

The money and scope rules of Follow the Money (2019 onward, seven parties, the return is the record) are settings of that one template and bind nothing else.

## Checking

Without checks a wrong answer looks the same as a right one, so checking is the fifth part and not support.

| What is checked | How |
| --- | --- |
| A register | Row counts against the source's own totals; sums against official figures where they exist; freshness; every row has a citation |
| A reading | A catch log: each document that could not be read is named, with the stage it stopped at. Nothing is set aside silently |
| The links | Error rate measured by how common the name is, on test pairs the registers themselves supply: two directors with one name on one company at one time are known to be two people |
| The review agent | Scored on those same test pairs before it is allowed to split anything on its own |
| A product | Tested when built. What fails becomes a card and a line on its known-limits page; it is not necessarily fixed |
| Follow the Money | Compared figure by figure with the frozen site. Every difference is explained by a card |

Repeated errors feed the rulebook. An error seen often is named as a class, carded with examples, and a build session writes a rule for it with a test against real rows. The rule then applies to new readings and to rows read before it existed.

## What this replaces

| Earlier design | This design |
| --- | --- |
| A stored person record that is merged and split | Links, decisions, and a grouping that is rebuilt |
| An identity module with an error bar to be ruled | A links table with a measured error rate by name band |
| Sixteen products, each its own service | Four shapes; each use case a template |
| Five kinds of module | Three: registers, links, products. Checking runs across all three |
| Arthur reviews suspicious joins and fires re-reads | A review agent splits; the scheduler runs re-reads |
| The press graph as the evidence around the registers | Parked. Journalism is searched by keyword; Papers Past is searched, with a broad name index |

Nothing a customer sees is lost. Three things are given up on purpose: fixing a person by hand, full independence between use cases that share a shape, and journalism as evidence about people.

## Support that does not change

The redesign leaves the machinery as already ruled. The record of each is in [Use Cases and Source Gaps](https://claude.ai/code/artifact/367e593a-8350-4bba-ba2d-b669ab0a4372).

- A new repository, QueryNZV4, with its data beside the old estate until the old has been consumed.
- Two boxes as peers, one scheduler for every job, four cards shared under the nine-rule protocol, a third machine as the voter for automatic takeover.
- The frozen Follow the Money site keeps its daily refresh and is the reference the new one is compared with.
- An off-site copy: a weekly full copy plus changes.
- Build sessions on node2, each in its own working copy, with one integrator that refuses a failing merge.
- The lessons flow, the card board, and the extraction rulebook kept from the press work.

## Changes to the terminal document

The terminal architecture of 20 August already describes this design: registers as the spine, and people as a view rebuilt from decisions. Five of its statements are changed by later rulings.

| It says | Now |
| --- | --- |
| Capture is robots-absolutist and ask-first | Capture is legal and polite (ruling 10) |
| Arthur is the deliberate bottleneck on judgments | Arthur is not in the loop; an agent reviews and splits (ruling 41) |
| No era is fired by anything but Arthur | The scheduler runs re-reads (ruling 45) |
| Products are built for partner entrepreneurs | The use cases drive the build; partners are an enhancement |
| Mentions and claims from journalism are a layer of the store | Parked with the press work |

## Still open

- [ ] How far a chain of links is trusted. Set after the first measurements.
- [ ] How much doubt a step through a person adds to a multi-step connection. Needed before the register scans.
- [ ] Whether the standby database copy waits for confirmation on every write. Recommendation: it does not.
- [ ] What counts as an emergency fix to the frozen site. Proposal: the release is broken or a published figure is wrong.
- [ ] The new operating rules, to be drafted for Arthur to change.
