# The news reader: a plan, and what is likely to go wrong

15 November 2026. For Arthur. Talk, not build: nothing here is started until he rules on the questions at the end.

## What it is for

There are 2.8 million articles from 177 sites in the old copy (nzherald.co.nz alone holds 779,702), and the provider's
estate-news copy walks them forward. The reader finds, in each article, the people and organisations it names,
the roles it gives them and what it says they did, so the registers can be joined to the media that mentions them.
It is not the news search (Arthur, 13 November: "dont build the news search").

## The one principle

**The reader records what the article says, and never decides who someone is.** A false match costs far more
than a missed one: a wrong link puts a named person beside something they never did (hard limit 14). So the work is
split into steps, and each step can only narrow what it was handed:

1. **Prepare** (no model). Take the body text alone, without its sidebars, captions or byline. Tag the section and
   article type, and find syndicated copies.
2. **Gate** (no model). Run the name-sightings pass that already exists (links/sightings.py), so only articles that
   name something in a register go to the model. This also orders the work.
3. **Read** (the local model). List every mention, verbatim, with its character offsets. For each one, record its
   kind, its role phrases and the organisation each role belongs to, *only where the text binds them*. Group the
   mentions that refer to the same person or body within this one article.
4. **Check** (no model). Every span must sit at its offsets, character for character. Every role-to-organisation
   binding must be backed by a sentence the check can point to. Anything else is downgraded to "unbound", never
   repaired.
5. **Link** (the links rules, separately). A mention becomes a candidate link to a register row only when a register
   corroborates it. Examples: the person's name together with an organisation the Companies Office lists them as a
   director of; an MP's name together with a portfolio that the Parliament register gives them on the article's
   date. Otherwise it stays an unlinked mention. Rulings 105 to 109 apply: measure, 20 pairs, Arthur rules. No fame
   priors (prominence never scores).

## What will go wrong, by kind

### A. Company names that are ordinary words
The Warehouse ("the warehouse" at a crime scene), Spark, Contact, Mercury (the energy company, the planet, the
element), Genesis, Meridian, Vector, Chorus, Z, Trustpower, Pioneer, Infratil, Harmoney, Zuru, Restaurant Brands,
Countdown, Freedom, Smiths City, Farmers. The Companies Office also holds many names like "Auckland Limited" and
"Solutions Limited". Vendors handle this by measuring how often a name occurs and treating a very common one as a
word (NewsCatcher's rule).

*Defence.*
- Measure every organisation form against the corpus. Any form that also occurs as an ordinary word is marked
  "needs an anchor".
- An anchored mention has at least one of: a legal suffix, NZX or a ticker, a named officer, an appositive ("Spark,
  the telco"), a sector word in the same sentence, or the article's own subject line.
- A form with no anchor is not read as the company.

### B. Brand, legal entity and group
- Pak'nSave and New World belong to Foodstuffs North Island Ltd or Foodstuffs South Island Ltd, depending on the
  store.
- "ANZ" can be ANZ Bank New Zealand Ltd or the Australian parent.
- Fonterra and Fletcher Building have dozens of registered companies each.
- "Canterbury" is a region, a rugby team and a clothing company.

*Defence.* Link to the group a register names, never to a subsidiary picked by the model. Keep the brand as printed.
The trading-name register (NZBN) does the mapping, not the model.

### C. Roles without a name, and roles without an organisation (Arthur's CEO case)
- "The chief executive said…" when the article names three companies.
- "Its boss", "the chair", "the spokesperson", "the minister", "the mayor", "the council", "the company", "the
  ministry".
- An article quoting two CEOs, one by name and one only by title.
- A local model also knows from training who runs Spark, and will "helpfully" fill the name in. Research on
  model coreference reports exactly this: content that is not in the input.

*Defence.*
- A role binds to an organisation only through one of these patterns in the text:
  - apposition: "Jane Smith, chief executive of X";
  - possessive: "X's chief executive Jane Smith";
  - pre-modifier: "X chief executive Jane Smith";
  - a short list of explicit forms like these.
- "The chief executive" with no binding in its own sentence or the one before stays *unbound*, along with the
  candidate organisations, and nothing downstream may pick one.
- A name that does not occur in the article fails the span check, whatever the model believes.
- Ministers and mayors are the exception, because a register holds them by date: "the Finance Minister" on
  3 March 2024 resolves from the Parliament register, not from the model.

### D. Time
- The role holds on the article's date, not today. A 2012 article's "Fonterra chief executive" is not Fonterra's
  chief executive now.
- These words change the meaning: "former", "then", "outgoing", "incoming", "acting", "interim", "designate", "who
  resigned last year", "will take over in March". Temporal-knowledge-graph work names a missing valid-from and
  valid-to as the largest single error class.
- 45 sites (7,877 articles) carry no date. Their roles cannot be placed in time.

*Defence.*
- Every role carries the article's date and a tense: current, former, acting, interim, incoming or designate.
- An undated article yields mentions but no dated roles, until the provider fills its date (practice 4, under way).
- An announcement date is not a start date.

### E. People's names
- **Shared names and partial names.** John Smith ×200, or a surname alone in later paragraphs. Initials, nicknames,
  honorifics (Sir, Dame, Dr, Hon), and married or maiden names.
- **Māori names.** Names shared across a whānau. Macrons printed or dropped (Tūhoe/Tuhoe; the sightings pass
  already folds them).
- **Names that are also words or places.** Hamilton, Nelson, Russell, Napier, King, Bishop, Grace, Hope, Rose, Wood,
  Price, Sharp, Love, Field.
- **Names inside other names.** These are not mentions of a person:
  - companies: Fisher & Paykel, Ryman Healthcare, Hugh Green Group, Mike Pero, Sir Peter Blake Trust;
  - sports grounds and venues: Eden Park, Peter Snell track;
  - schools and colleges: Wellington College;
  - case names: R v Smith;
  - bills: "the Smith Bill";
  - streets: Jervois Road, Ponsonby Road, Lambton Quay.
- **Racing pages.** Horses' and greyhounds' names, and trainers'.
- **Wire stories.** AP, Reuters, AAP and the Guardian name overseas people, and some will share a name with a NZ
  director or donor.

*Defence.*
- The longest form wins (the sightings pass already does this), so a name inside a longer organisation, place or
  road form is not a person.
- Mark wire stories by their dateline and credit line. Their people are never linked to New Zealand registers
  without an anchor, or are not read at all (question 3).
- A surname-only mention links only through its own article's cluster to a full name.
- One name with no anchor is never linked, however rare it is.

### F. Places and metonymy
- "Wellington" can mean the Government.
- "Auckland" can be the council, the region or the team; "Canterbury beat Otago" is about rugby teams.
- "Queen Street retailers", "the Beehive" and "the Crown" stand for other things.
- Some places are also companies: Napier Port, Port of Tauranga, Wellington Airport.
- Iwi have names and also legal bodies: Ngāi Tahu, Te Rūnanga o Ngāi Tahu, Ngāi Tahu Holdings. Taranaki is an iwi
  and a region.
- "The council" leaves open which council.

*Defence.*
- The reader types each mention as place, organisation, team or government by its use in the sentence, and keeps
  the place reading when unsure.
- An iwi links to a post-settlement entity only when the article names that entity (the iwi directory register
  holds them).
- "The council" binds only to a council the article names.

### G. Law and ethics: the hard part
- **Name suppression.** An article may say "a man who cannot be named" or "a prominent businessman". A suppression
  can also be ordered *after* an article named someone, and later articles respect it while the early one does not.
  Under NZ law a name includes any particulars likely to identify, which is jigsaw identification. In February 2025
  Google's AI was found naming suppressed people.
  - Never resolve a "cannot be named" description to anyone.
  - Never link the identifying details around it.
  - Check every person linked from a court story against the courts lane's suppression flags. An article from
    before a suppression yields no link for that person.
- **Allegation is not conviction.** Each of these is recorded as printed and never merged with the others:
  arrested, charged, accused, denies, pleaded guilty, convicted, acquitted, charges dropped, discharged without
  conviction.
- **Corrections and retractions.** An updated article replaces its earlier reading. A retraction withdraws it.
- **Who wrote it.** An opinion column's author is its writer, not its subject. In a letter to the editor, the writer
  is a private person.
- **Children, victims, people named in passing.** They are kept as the text gives them (ruling 176), but are never
  linked without an anchor.
- **Addresses** ("of Riccarton", "a Mt Albert man") are kept in the private table, never shown (hard limit 15).

### H. The article around the text
Each of these needs handling:
- "Related stories" and "most read" panels, which name other people.
- Photo captions, which may name people not in the story.
- Bylines and "additional reporting".
- Paywall stubs (being refetched by 21 November).
- Live blogs: hundreds of names over hours.
- Market wraps: 30 companies with tickers. These are useful, but each company is a mention, not a story about it.
- Death notices, sports results tables, and press releases republished whole (on Scoop the "author" is the
  organisation).
- The same story on several sites. NZME runs one story on the Herald and its regional papers, and RNZ and Stuff
  share copy. One story is counted once, by corroboration tier.

*Defence.* Preparation strips each panel by site profile, one profile per site family, written before the reader
(profiles before readers). It also finds near-duplicates by text, and tags each article's type.

### I. The model itself
- **Invented spans.** Defended by the span check in step 4.
- **Filling in from its own knowledge.** Defended by the span check and the binding rule (C).
- **Dropping mentions in long articles.** Recall falls in the middle of long contexts ("lost in the middle"), so
  long articles and live blogs are read in overlapping pieces.
- **Wrong canonical names.** It finds the right person but writes the wrong full form. Defended because the span is
  verbatim and canonical names come from the registers, never from the model.
- **Instructions inside an article.** Article text is data, never instructions.
- **A different answer on the next run.** One frozen reading per article, kept and stamped (ruling, 24 September).

### J. Scale
At the courts reader's rate, 2.8 million articles would take months. The gate (step 2) sends only articles that
name a register row, and the order is set by Arthur (question 4). Every article that goes through is read whole.

## How we know it works before it runs

- **A test set.** About 300 NZ articles, labelled by hand and stratified by kind: business, courts, politics, local
  government, sport, racing, wire, opinion, market wraps and live blogs. It is seeded with the hard cases above:
  - The Warehouse as a word;
  - three CEOs in one article, one of them unnamed;
  - "former" and "acting" roles;
  - a suppressed defendant;
  - a wire story naming a namesake;
  - a horse called after a person.
- **Measured separately:** mention recall, span exactness, role-to-organisation precision, and link precision.
  Release requires role binding and link precision near 100%, with recall second. An unbound or unlinked mention
  is a cost we accept; a wrong one is not.
- **Then the links method.** 20 pairs per new rule, and Arthur rules.

## Questions for Arthur

1. **What the reader extracts.** People, organisations and roles only. Or also what the article says they did
   (charged, appointed, donated, won a contract)? I recommend roles first and events second, because events carry
   the defamation risk.
2. **Sport, racing and entertainment.** Read them and tag the section, or leave them out? I recommend reading
   sport (directors and owners appear there), but leaving out racing results and TV listings.
3. **Foreign wire stories.** Leave them out, or read them with no link to New Zealand registers unless a mention is
   anchored? I recommend reading them unlinked.
4. **Order.** Newest first, or articles that name the most register rows first? I recommend newest first within
   the gate.
5. **Suppression as a ruling.** "A description the article gives in place of a suppressed name is never resolved,
   and a court story's people are checked against the courts lane's suppression flags before any link." I
   recommend making this a hard rule.

## Sources

- Entity linking and ambiguity: [Wikipedia](https://en.wikipedia.org/wiki/Entity_linking);
  [NewsCatcher, entity disambiguation](https://www.newscatcherapi.com/docs/news-api/guides-and-concepts/entity-disambiguation);
  [news entity linking errors (Dagstuhl, LDK 2019)](https://drops.dagstuhl.de/storage/01oasics/oasics-vol070-ldk2019/OASIcs.LDK.2019.14/OASIcs.LDK.2019.14.pdf);
  [a fair and in-depth evaluation of entity linking](https://ar5iv.labs.arxiv.org/html/2305.14937)
- Models and coreference: [low-hallucination coreference with LLMs (EMNLP 2025)](https://aclanthology.org/2025.findings-emnlp.934);
  [actor identification in discourse](https://arxiv.org/html/2402.00620v1)
- Adverse-media false positives: [USPTO, contextualised entity resolution](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12481667);
  [Quantifind](https://www.quantifind.com/resources/sanctions-screening-intelligent-entity-matching/)
- Metonymy: [SemEval 2007 metonymy task](https://aclweb.org/anthology/S07-1007.pdf);
  [Leveling, location metonymy](https://user.geo.uzh.ch/rpurve/gir06/papers/individual/leveling.pdf)
- Macrons: [Relab, Māori character search](https://help.relab.co.nz/en/news/3207-mori-character-search-support-);
  [AddressFinder](https://addressfinder.com/blog/macrons-now-supported-in-address-search)
- Name suppression: [RNZ, Google's AI breaching suppressions](https://www.rnz.co.nz/news/national/542063/google-s-ai-has-been-breaching-new-zealand-court-name-suppressions);
  [2017 NZSC 59](https://courtsofnz.govt.nz/assets/cases/2017/2017-NZSC-59.pdf);
  [BSA, jigsaw identification](https://www.bsa.govt.nz/decisions/all-decisions/wicks/)
- Time: [ATOM, temporal knowledge graphs](https://arxiv.org/pdf/2510.22590);
  [temporal edges](https://dev.to/hannune/temporal-edges-in-knowledge-graphs-why-static-edges-break-graph-rag-1ll)
- Long documents: [lost in the middle](https://arxiv.org/pdf/2307.03172);
  [assessing the quality of information extraction](https://arxiv.org/pdf/2404.04068);
  [recall them all](https://arxiv.org/pdf/2405.02732)
