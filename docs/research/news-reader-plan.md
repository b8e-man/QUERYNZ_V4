# The news reader: a plan, and what is likely to go wrong

15 November 2026. For Arthur. Talk, not build: nothing here is started until he rules on the questions at the end.

## What it is for

There are 2.8 million articles from 177 sites in the old copy (nzherald.co.nz alone holds 779,702), and the provider's
estate-news copy walks them forward. The reader finds, in each article, the people and organisations it names,
the roles it gives them and what it says they did, so the registers can be joined to the media that mentions them.
It is not the news search (Arthur, 13 November: "dont build the news search").

## The one principle

*Second round, 15 November: the read extracts and does not link. Step 5 and the Correlation section below are
work for after the read ("Extraction first", further down).*

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

## Arthur's answers (15 November 2026)

Arthur: "dont build, just use this for further planning and interviewing".

1. **Scope: be ambitious, question later.** Read people, organisations, roles *and* events (what the article
   says they did), and add **sentiment**.
2. **Sport and entertainment** are read.
3. **Foreign wire stories** are read, and not linked to New Zealand registers unless a mention is anchored.
4. **Order: newest first, to keep things fresh, then walk back.**
5. **No suppression rule in the reader.** It would complicate things. A suppression register suppresses before
   export. (Section G's suppression defence is withdrawn from the reader; G's other points stand as written until
   discussed.)
6. **Correlation by article-wide themes.** Step 5 links by *theme tags* as well as anchors, in the horse farm
   pattern (rulings 153 and 157). The Warehouse appears in NZ media too often without any of section A's anchors,
   so the link needs either rich anchoring or themes. One theme alone is not reliable: "retail" fits The Warehouse,
   but also a warehouse burglary at a retail park. What is obvious to a person is not to a machine, so the system
   needs **many kinds of correlating evidence**. This also helps the other links, and the names that are something
   else (section E).

## Correlation: theme tags and the other evidence (planning, from Arthur's point 6)

Correlation means the article and a register row agree on things *other than the name*. No single agreement is
proof; a link is made by a rule that names the combination it needs, measured on 20 pairs (rulings 105 to 109).

### The evidence kinds

1. **Themes, on both sides.** The reader tags each article with themes from one vocabulary. Each register row gets
   themes from the same vocabulary, derived from what the register itself says:
   - companies: their industry code (BIC, which maps to ANZSIC). We do not hold it yet; the NZBN register carries
     it where the company gave it. This is a question below;
   - charities: main_sector and charitable_purpose;
   - grants: category_1 and category_2, and the purpose as published;
   - tenders and award notices: the GETS product categories;
   - Commerce Commission cases: industry and category;
   - insolvency: industry;
   - the iwi directory: primary_purpose;
   - councillor and MP interests: their declared category.
   
   A candidate whose register themes overlap the article's gains evidence; one whose themes contradict loses it.
2. **Co-mentions through the registers (the horse farm, widened).** The article names other things the registers
   tie to the candidate. For The Warehouse, that could be its subsidiaries (Noel Leeming, Torpedo7), its directors
   or officers, or its NZX code. One article naming two things one register ties together is far stronger than
   either alone.
3. **Place.** The article's places against the candidate's registered office, its trading places, and its
   council or electorate.
4. **The sentence itself.** Capital letters mid-sentence; "The Warehouse's"; "at The Warehouse"; "The Warehouse
   Group"; a role binding (section C).
5. **The article's own frame.** The headline, the site's section (business, sport, local), the article type, and
   the dateline.
6. **Time.** The candidate existed on the article's date (it was incorporated before it and not removed), and the
   person held the role on that date.

### Why themes alone fail, and the defence

- **One theme says little.** "Retail" fits The Warehouse and a burglary at a retail park. A theme is
  evidence only when it is *specific* (bloodstock is specific; "business" is not) and *agrees with another kind*
  of evidence (co-mention, place, sentence).
- **Contradicting themes count.** "Crime", "a warehouse fire" or "logistics" against a retailer lowers the score.
- **A specific thing in the article may be the only link** (the horse farm). A distinctive trading name ties to
  its owner through the register, with or without the owner's name.
- **Themes are tagged per article *and* per paragraph.** Live blogs and round-ups carry many themes; the theme
  nearest the mention counts most.

### The vocabulary

- **For articles:** IPTC Media Topics, the news industry's free standard: over 1,200 terms in a five-level tree,
  revised yearly. Its upper levels are broad; its lower ones are specific enough to matter (for example horse
  racing and equestrian).
- **For business sides:** ANZSIC, through BIC, which is New Zealand's own classification.
- **A map between the two is ours to write.** Kept as a table, measured and corrected like any rule.

### Names that are something else (section E), by the same evidence

- Hamilton, the city or the person: the city's council and places are co-mentioned; the person's register roles
  match the article's themes.
- A horse called after a person: the themes are racing and bloodstock, and the person has no register tie to
  them.

### A tension to raise

How often a company appears in the media is a fame prior, and Arthur's ruling is that prominence never scores.
Correlation must therefore use only what the article and the registers say, never how often a name is reported.
**Question:** does that ruling hold here, or does Arthur mean a company's frequency in the media may count?

## Sentiment (planning, from Arthur's point 1)

- **Sentiment is per mention, not per article.** One article can praise one company and criticise another.
- **Three sentiments differ:**
  - the article's tone toward the entity;
  - what someone quoted says about it;
  - the entity's own words.
  
  These are recorded separately.
- **Research says news is hard:** opinion is implicit, and document-level and sentence-level labels do not
  predict overall entity sentiment well. The headline's tone does correlate with the entity sentiment, so the
  headline is read with it.
- **Reported events are not sentiment.** "Charged with fraud" is an event of the kind charged, not the article's
  opinion. Keep the event and the sentiment apart, or sentiment becomes a back door for allegations.
- **A scale:** negative, mixed, neutral or positive per mention, with the sentence that carries it. The test set
  labels it, and release needs agreement with a person's reading.

## Events (planning, from Arthur's point 1)

- **The kinds:** appointed, resigned, charged, convicted, acquitted, fined, won a contract, donated, acquired,
  went into liquidation, sold, sued, and so on.
- **Each event carries:** its participants and their roles in it, the date the article gives, and its *modality*
  (happened, alleged, denied, planned, rumoured).
- **The kinds come from the registers we have.** An event of a kind a register also records (an appointment, a
  liquidation, a contract award) is checked against that register.

## Arthur's second answers (15 November 2026)

- **Extraction first, links later.** "Be less focused on making links and more on extracting a robust set of data
  from the articles and playing around with links after." The read makes no links. Everything about linking
  (step 5, Correlation) waits.
- **Quotes are extracted.**
- **Authors go into a register,** with whatever data can be had on them.
- **Industry codes:** yes, the companies' BIC codes are to come from the NZBN register (planned, not started).
- **Vocabulary:** use what exists (IPTC Media Topics, ANZSIC), and build our own only if needed.
- **Sentiment is for everything above and more:** media monitoring, and audience segmentation and analysis among
  others. So it is kept fine-grained (per mention, per quote, per paragraph), never collapsed to a score per
  article.
- The prominence and link-bar questions fall away with the links.

## Extraction first: what each article yields

One frozen reading per article. Every item is verbatim with its character offsets, so any later use, linking
included, can go back to the text. Identifying details go to the private table as printed (ruling 176).

1. **The article.**
   - Site, address, headline, standfirst, section.
   - Type: news, opinion, letter, review, obituary, press release, live blog, market wrap, sponsored, correction.
   - Dateline, and the published and updated times.
   - Wire or agency credit, syndication group, correction notes, word count, and any te reo Māori passages.
2. **Its authors.** Every byline as printed, its role line ("senior reporter"), outlet, agency, "additional
   reporting by", a columnist's bio line ("X is a former …"), and contact details as printed.
3. **Themes.** IPTC Media Topics, for the article and for each paragraph.
4. **Mentions.**
   - People, organisations, places, brands and products, and things: farms, ships, horses, buildings, roads,
     events and awards.
   - Each with its kind as used in the sentence, and grouped with the other mentions of the same person or body
     within this article.
   - Role phrases, with the organisation as the text binds it, and their tense (current, former, acting, interim,
     incoming).
   - Descriptors as printed: age, town, occupation.
5. **Relations the text states.** "X's subsidiary Y", "X, husband of Y", "X owns Y", "X bought Y". These are
   recorded as the article's claim, not as a link.
6. **Quotes.** Each one records:
   - the words, verbatim;
   - its form: direct, partial, indirect (paraphrase) or mixed;
   - the speaker as printed (a name, a pronoun, a role, "a spokesperson", "a source");
   - the speaker's group within the article, and the organisation the text gives them;
   - the verb (said, claimed, admitted, denied);
   - the channel (an interview, a statement, court, social media, an earlier article);
   - whom or what it is about.
7. **Events.** These record:
   - the kind (appointed, charged, fined, won a contract, liquidated and so on, from IPTC and the kinds the registers
     record, all of them, ambitious);
   - the participants and their part;
   - the date and place;
   - the modality: happened, alleged, denied, planned or rumoured.
8. **Numbers with what they measure.** Money, salaries, fines, contract values, shares, votes and job losses, each
   tied to its subject in the text.
9. **Sentiment.** Recorded per mention and per quote, kept in three kinds:
   - the article's tone toward the entity;
   - what the quoted person says about it;
   - the entity's own words.
   
   It also records the sentence that carries it, and the headline's tone.

## The author register

**What it holds for each author:**
- Every name form, and each outlet with the first and last date of their bylines.
- The roles they state, their bio lines, co-authors, and contact details and social handles as printed.
- Their **beats**, which are the themes of their own articles over time (from item 3).

**Where it comes from:**
- The bylines, in the articles' own metadata and text.
- Each site's author pages, if the provider captures them (question below).
- Bylines in the old copy are often missing: 227 of a 400-article sample had no author. The provider now fills
  them from the page (practice 4, under way).

**Its pitfalls:**
- Some bylines are not people: "Herald staff", "RNZ", "Open Justice reporters", "AAP".
- One story can carry several bylines plus additional reporting.
- Two journalists can share a name, and some write under a pen name.
- Photographers' credits can be mistaken for bylines.
- A guest columnist is a person in other registers too (a former MP, a chief executive). Their bio line is the
  richest data on them, and it is recorded as they state it.

## Quotes: what goes wrong

The research corpora are DirectQuote (10,279 direct quotes), FRACAS (10,965 attributions, direct and indirect) and
Quotebank (178 million articles, machine-labelled). They agree on the hard cases:
- **Indirect quotes** are paraphrased and have no quotation marks.
- **A speaker who is only a pronoun** ("she said") needs the article's grouping of mentions.
- **A quote running over several paragraphs** opens a quotation mark on each paragraph and closes only at the end.
- **Quotes inside quotes; scare quotes** ("so-called 'reform'"), which are not speech; and **headline quotes**,
  which are shortened and need matching to the body.
- **Recycled quotes:** "told the Herald last year" is an earlier article's quote, with its channel recorded.
- **Statements by an organisation** ("a spokesperson for X said"). The speaker is the organisation, and the person
  stays unnamed.
- **Unnamed sources** ("a source close to the company") are recorded as such, never filled in.
- **Te reo Māori quotes and their translations** are recorded as a pair.
- **An invented quote or speaker** fails the span check: the words must be in the text.

## Questions for the next interview

1. **Author pages.** Should we ask the provider to capture each news site's author and profile pages (beat, bio,
   contact as published) for the author register?
2. **Letter writers.** Letters to the editor are written by private people. Do they go into the author register
   like journalists, or are they kept only as the article's own data?
3. **Audience segmentation.** What audience is meant: the readers of each outlet, inferred from what it publishes;
   the people the articles are about; or the customers of a product we sell? It sets what the reading has to
   capture beyond what is listed above.

On the first round's question 6 ("which kinds of event come first"): it was too vague to be worth Arthur's time.
With the scope ambitious, every kind is read, so there is no first kind to choose.

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
- Themes: [IPTC Media Topics](https://iptc.org/standards/media-topics/);
  [IPTC NewsCodes](https://iptc.org/std/NewsCodes/guidelines/);
  [BIC codes on the NZBN register (OIA response)](https://fyi.org.nz/request/18515-list-of-new-zealand-businesses-based-on-bic-codes);
  [ANZSIC](https://Www.Wikipedia.org/wiki/ANZSIC)
- Sentiment: [open-domain targeted sentiment](https://arxiv.org/pdf/2204.06893);
  [entity-level sentiment survey](https://aitopics.org/doc/arxivorg:E5088E31);
  [headline tone and entity sentiment (BSNLP 2023)](https://aclanthology.org/2023.bsnlp-1.10.pdf)
- Quotes: [DirectQuote (LREC 2022)](https://ar5iv.labs.arxiv.org/html/2110.07827);
  [FRACAS](https://ar5iv.labs.arxiv.org/html/2309.10604);
  [German news quotations (KONVENS 2024)](https://aclanthology.org/2024.konvens-main.22.pdf)
- Long documents: [lost in the middle](https://arxiv.org/pdf/2307.03172);
  [assessing the quality of information extraction](https://arxiv.org/pdf/2404.04068);
  [recall them all](https://arxiv.org/pdf/2405.02732)
