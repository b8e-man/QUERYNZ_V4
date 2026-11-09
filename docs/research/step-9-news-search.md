# Step 9, tranche 7: the news search (design, 9.3 and 9.4)

Written 10 November 2026 by stream D of the step 9 integrator session.
Design only: no index is built, because the corpus is not copied yet
(tranches 3 and 4 wait for Arthur's look at the two sources). Nothing here
is a ruling. The legal position it works under is
`docs/legal/positions/news-articles.md` (a draft for the lawyer). Every
model it uses runs on the boxes (hard limit 10).

## The shape in five lines

1. The lane `news` builds a tantivy keyword index over its verbatim tables,
   on the boxes, as `registers/papers_past/index.py` already does.
2. After stage 1, the report turns its own records into probes: the
   subject's names, its companies, trading names, bodies, roles, co-officers
   and places of record, each with the row it came from.
3. Names and things are searched as phrases; each hit is judged against the
   whole probe set, by exact spans re-read in the article text.
4. A name alone is "an article that mentions this name"; a name plus a thing
   from the subject's own records is a connection; a thing the registers tie
   to the subject is a connection by that link, name or not (the horse farm).
5. The report shows a headline, publisher, byline, date, link and a short
   excerpt, never the article; nothing is written to the links.

## What the estate already has, reused

- **The engine.** `registers/papers_past/index.py` (build) and
  `registers/papers_past/search.py` (read): tantivy, text not stored, a hit
  is a key read back through the catalogue, fast `day` and `paper` fields,
  a 320-character window around the first word asked (`SNIPPET`), one index
  opened per process under a lock. Arthur chose tantivy on 2 November
  ("use tantivity and go"); FTS5 stays the measured alternative. The news
  index is the same build with `publisher` for `paper`.
- **Embeddings.** `support/scheduler/embed.py` (`qv4-embed`): chunks of
  1,500 characters with 200 overlapping, vectors through
  `support.modelclient.embed()` to the `embedding` profile (bge-m3,
  `support/scheduler/profiles.toml`), stored as a reading keyed by the
  document's hash (ruling 50). Its piece reads a landed document by sha256;
  the news lane needs a piece that reads an article's text from its table
  instead, same chunker, same store.
- **Name folding.** `products/report/search.py` (macrons folded, every word
  begins a word; copied from the board and held equal by a test),
  `links/rows.py` (`member_name`, `fold`, the honorifics and post-nominals).
- **The address test.** `products/report/rules.address_shaped` (ruling 102).
- **Suppression.** `pub` views replace a suppressed name; the whole names
  sit in the lanes' private schemas (`courts_private.withheld_names` and the
  like), which a product never reads.

Imports run one way: a product imports only `support/`. So the read side of
the tantivy index (open, query, window) moves to `support/textindex/`, used
by `registers/papers_past/search.py`, `registers/news` and the report alike.
That move is the integrator's to take or refuse; the fallback is the
report's own copy held equal by a test, as `products/report/search.py` is.

## The module

**Lane side, `registers/news/`** (the lane 9.2 creates):

- `columns.toml`: for each copied table, which column is the headline, the
  body, the date, the publisher, the byline, the publisher's address and the
  key. A mapping, not a reshaping: the tables stay verbatim.
- `publish.sql`: `pub.news_articles` (ref `news:<table>/<key>`, publisher,
  published_on, headline, byline, url, chars, text, `text_sha256`, and the
  ruling 102 flag `text_address_shaped`). `text_sha256` is of the body after
  whitespace is collapsed; articles that share it are one article published
  in several places (syndication), shown once with "also at".
- `index.py`: the tantivy build, `qv4-news-index`, low priority, batched,
  never a whole-store scan (1 November). Fields: `ref` (stored), `headline`,
  `text` (indexed, not stored), `publisher` and `day` (fast). The tokenizer
  folds macrons and case, as Papers Past's.
- `spans.py`, `qv4-news-suppressed-spans`: inside the boxes, every name the
  estate holds as suppressed is searched as a phrase over the index, and
  each hit's character offsets go into `pub.news_suppressed_spans` (ref,
  start, end): offsets only, never the name. Rerun after the courts lane
  records a new order.
- Embeddings (optional, after keyword is measured): `qv4-news-embed`, the
  `embed.py` chunker and store; one query is embedded on the processor.

**Report side, `products/report/news.py`**, called from `stage1.walk1`'s
result, after the stage-1 records are built (ruling 154):

    news(conn, w: dict, index) -> {"news": [items], "news_results": [Papers Past items], "news_stats": {...}}

Inputs: the walk `w` (its `members`, `roles`, `entities`, `stage1` bucket
and each item's `row`), `pub.news_articles`, `pub.news_suppressed_spans`,
`pub.company_lookups.trading_names`, and the index. Output: a `news` bucket
of report items (below), shown under its own section and counted in the
memo; nothing is written to the database.

## The probes, from the stage-1 records

Each probe is `{text, kind, origin_ref, hop, dates, distinct}`.

| Kind | From | Searched alone? |
| --- | --- | --- |
| name | the subject's confirmed rows (`w["members"]`, the start row): each name form the rows print, folded; an MP's roster aliases | yes |
| company | hop-1 organisations (`w["entities"]`, stage-1 hop 1), current and former names, "Limited"/"Ltd" made optional | yes, if distinctive |
| trading name | `pub.company_lookups.trading_names` of the hop-1 companies; a charity's `other_names`; a Commerce Commission party's `trading_as` | yes, if distinctive |
| body | the societies, charities, parties, iwi bodies, boards and agencies on the subject's own rows | yes, if distinctive |
| role | the role titles on the subject's rows, paired with their body ("director of X", "chair", "trustee") | no: corroborates only |
| co-officer | hop-2 people on the subject's own organisations (stage-1 `people`, hop 2) | no: corroborates only |
| place of record | the registered office town of a hop-1 company (`company_addresses`, a company's registered office only) | no: corroborates only |

- A name from a suppressed row is never a probe (hard limit 16); the count
  of such rows is in the stats, never the name.
- **Distinctive.** A thing probe is searched alone only if, with the legal
  suffix gone, it keeps two words or one word that is not in a list of
  common words, and its hit count in the index is under a ceiling (to be
  measured; start at 2,000). A probe over the ceiling is counted in the
  stats as "too common to search alone" and still corroborates.
- Hub organisations (stage 1's `hubs`) are probes, but their people are not
  co-officers: a hub's 50+ people would corroborate by chance.

## How a hit is judged (9.4)

For each article any searched probe hits, every probe is tested against
the article's text by exact folded phrase, and each match is recorded as
evidence `{probe kind, text, origin_ref, offset}`, re-read from the text,
not taken from the index's word.

- **mention:** a name probe matches and nothing else does. Shown as "an
  article that mentions this name". Never a link to the person.
- **connection:** a name probe matches and at least one company, trading
  name, body, role, co-officer or place of record from the subject's own
  records matches too, inside the date window below. Shown with the
  evidence: "names <subject's name> and <thing>, which <register> ties to
  the subject".
- **connection through a register (the horse farm):** a distinctive company,
  trading name or body from the subject's own records (hop 1) matches, with
  or without the name. The article is connected to the subject by the
  register's link, carried as `via` = the organisation's ref and the
  link's rule. A thing only stage 1's hop 2 reaches makes a near item, with
  stage 1's reason (a connection through a person), never confirmed.
- **Date window.** A role corroborates only for an article dated from a
  year before the role began to a year after it ended; a company only
  within a year of its registration to a year after its removal. Outside
  the window the match is kept as evidence and does not grade.
- A co-officer, a role or a place without the name never makes anything.
- **Order.** Connections first, newest first; then mentions. Mentions are
  listed to 20 and the rest counted. If embeddings are built, mentions are
  ordered by similarity to a text made from the subject's records; a vector
  orders, it never grades.
- **Papers Past** (hard limit 17): the subject's name probes only, shown in
  `news_results` as search results with the excerpt; never judged, never a
  connection, never stored.

## The item

`{ref, view: "news_articles", kind: "article", title: headline, publisher,
byline, date, url, excerpts: [{text, offset}], grade: "mention" |
"connection" | "near", reason, rule, via, evidence, also_at, flags}`.

The excerpt is the 320-character window around the first evidence span,
and at most one more around a second, so no item carries more than 640
characters of text. A window that overlaps a suppressed span has that span
replaced by "name suppressed"; a window that is address shaped is not
shown, and the item says an excerpt was withheld. The text whole stays in
the view and never enters the item.

## The checks that can fail

Each runs against real data once the corpus is copied (ruling 244).

1. **Index complete.** Documents in the index equal rows in
   `pub.news_articles`, table by table.
2. **Round trip.** For 200 sampled articles, a six-word phrase taken from
   the text finds that article in the top ten.
3. **Folding.** "Maori" finds a "Māori" article, and the other way.
4. **A name alone never connects.** No item graded connection lacks an
   evidence entry other than a name.
5. **Evidence is real.** For every evidence entry, the article's text at its
   offset equals its folded text, and its `origin_ref` is in the report's
   own records (guards against a check that passes by doing nothing).
6. **The horse farm, on a real subject.** One connection through a register,
   with no name in the article, shown on a named subject ref (tranche 7's
   acceptance); and the same article run against a subject not tied to the
   thing gives no item.
7. **Suppression.** A subject with a suppressed row issues zero probes from
   it; no shown excerpt overlaps a row of `pub.news_suppressed_spans`.
8. **Address.** No shown excerpt is address shaped; a test article holding
   an address shape has its window withheld.
9. **Never whole.** No item's excerpts exceed 640 characters.
10. **Papers Past.** Every `news_results` item is a result; nothing in
    `products/report/news.py` writes, and nothing in `links/` imports it.
11. **Nothing silent.** Listed plus counted equals hits, per grade; every
    probe too common to search alone is counted.
12. **Local only.** The index and any embedding call reach only the boxes'
    own addresses.
13. **Precision, measured.** Twenty connections sampled and read in a
    session (samples only, hard limit 11), the way links rules are measured
    (rulings 105 to 109); Arthur rules on the result.

## Open, for the integrator or Arthur

- `support/textindex/` versus a held-equal copy (above).
- The thing ceiling and the common-word list, measured on the copied corpus.
- Whether connections are ever stored. This design keeps them in the report
  only (hard limit 14).
