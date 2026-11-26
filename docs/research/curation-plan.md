# Curation: a personal feed ruled by register records and subjects (design, not built)

Arthur, 26 November 2026: "i want to create a curation feature. let's do some planning". Still being designed:
"we wait for now as we are still planning and designing". Nothing here is built until Arthur says so.

## What it is

Arthur, 26 November 2026: "What we really want is to be able to select an entity and create a feed with relevant news
about them. We want it to start broad and be able to narrow it down. we will use it to filter all documents and be
able to exclude documents based on source and type. for example, we might want to include hansard reports and council
minutes and GETS. but we might want to specifically exclude auckland city council minutes".

- **A feed is made from an entity:** Arthur selects a register record (a company, person, charity or body) and a feed
  is created for it. Many feeds, one per entity or purpose ("we will be spawning multiple feeds").
- **It starts broad and is narrowed:** at first everything related to the entity; then narrowed by relation, subject,
  document type and source.
- **It filters all documents**, not news only: news, Hansard, council minutes, GETS (tenders), the Gazette and the rest.
- **Narrowing by type and by source:** include or exclude a document type (Hansard, council minutes, GETS), and within
  a type a source (Auckland Council's minutes, one news site).
- **A media monitoring feed:** newest first.
- **Subjects** narrow (or widen, see below) a feed too: a subject is typed freely or picked from those the readings hold.

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
8. A subject is typed freely or picked from the subjects the readings hold, both; a typed subject catches its other
   forms ("3D printing" catches "3D-printed").
9. One subject, several signifiers: "Itaewon disaster" and "Seoul crowd crush" are one subject with two names; a subject
   is kept with its signifiers.
10. Newest first: "this is a media monitoring feed". Every item carries its own date.
11. Many feeds, each made from an entity (decision 1 above stands: a possible match is kept out).
12. Every document type, not news first; narrowed by type and by source.
13. Broad includes subjects: a feed starts with the documents on its entity's subjects that never name it (a
    Fonterra feed carries dairy prices).
14. Register rows are items beside documents, by their link to the record (a GETS award, a Gazette notice, an
    appointment).
15. Every document type gets a reading profile, so every relation works on every type; read documents only, as for news.
16. The name pass is added to every type it lacks: news, council minutes, the Gazette, GETS (today it runs on Beehive,
    Hansard, Parliament and the courts only, links.sightings.LANES).

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

- **An entity's subjects:** where a feed's subjects come from (the subjects of the documents that name the entity,
  the most frequent first; what its register says it does, an industry code; or both), and how many it starts with.
- **Sources per type:** the name of a source in each type (a council, a news site, a ministry), so it can be excluded.
- **Profiles owed:** which types have none yet, and their order.
