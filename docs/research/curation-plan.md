# Curation: a personal feed ruled by register records and subjects (design, not built)

Arthur, 26 November 2026: "i want to create a curation feature. let's do some planning". Still being designed:
"we wait for now as we are still planning and designing". Nothing here is built until Arthur says so.

## What it is

- **Curated:** news articles first (other documents later), filtered by their relation to an entity.
- **Produces:** a personal feed (the board's paper, showing only what the rules let in).
- **Curated by:** rules Arthur writes, on a form on the board.
- **An entity is a register record** (a company, person, charity or body), not a name as written.
- **Or a subject:** a rule takes a record or a subject, to include or mute.

## Relations a rule can ask for

| Relation | Judged by |
| --- | --- |
| Named in it | the record's name found in the text (the links lane's name sightings) |
| Central to it | in the headline, named several times, or quoted |
| In a role | the reader has it quoted, holding a role, or in an event |
| Connected to it | the article is about a record one step from it in the registers (a company's directors, a director's companies) |

## Decisions (Arthur, 26 November 2026)

1. A name that fits several records ("possible") stays out of the feed, listed in a "possible" panel with its candidates.
2. Rules match read articles only.
3. Connected is one step out.
4. "Subjects" replaces "themes" in everything said and shown.
5. Subjects go deeper than the IPTC labels: the specific things an article is about, each with a kind (an event: the
   2022 Seoul crowd crush; a technology: 3D printing; a product or work: Call of Duty; a law or bill; an issue or
   programme). Arthur's examples: "Hundreds of 3D-printed guns seized" lacks 3D printing; "'Call of Duty' slammed for
   using real Seoul crowd crush footage" lacks the crowd crush.
6. A specific subject the text does not name outright is kept, marked inferred, with the article's own words beside it.
7. Re-reading the articles already read: decided later.

## Steps, as designed

| Step | What | Where |
| --- | --- | --- |
| 0a | Subjects shown: under the inspector's headline; the paper's tags and sections | products/board/news.py, paper.py |
| 0b | The reader finds deeper subjects; a gate checks each against the text | registers/news/gold/trial.py (prompt), read.py (READER 6), gates.py |
| 0c | Trial: the gold set (32 labelled articles) and Arthur's two examples; Arthur judges about 20 in the review tab | registers/news/gold |
| 0d | The articles already read, read again (decision 7) | qv4-news-read |
| 1 | News sightings: the deterministic name pass over articles; a sample of about 2,000 first, measuring how often a name fits several records | links/sightings.py |
| 2 | Article → record: each name the reader extracted tied to the records it is sighted as; one record tied, several "possible" | links.news_entities, pub.news_entities |
| 3 | Rules: a feed tab, a form (record or subject, relations, include or mute, optional desk or site); a ledger, a withdrawn rule marked, never erased | products/board/feed.py, `<live>/board/feed-rules.jsonl` |
| 4 | Matcher: each rule's articles and why, after each news-read row and each links build | job qv4-feed-match, pub.feed_items |
| 5 | The feed: the paper's layout, each story saying why it is there | products/board/paper.py |
| 6 | Connected: one step through the links tables | the matcher |

## Still to design

- Subjects as rules: how a subject is chosen (free text, or from the subjects the readings hold), and whether "3D
  printing" also catches "3D-printed".
- How a subject is matched across articles (the same event named differently by two sites).
- How the feed orders stories (newest first, or by how strongly they match).
- Several feeds, or one.
