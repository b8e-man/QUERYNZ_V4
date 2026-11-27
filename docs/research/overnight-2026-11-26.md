# Overnight 26 to 27 November 2026: the curation build

Arthur, 26 November 2026, 21:00: "I am going to bed. do the build while i sleep." The design:
docs/research/curation-plan.md. One line a close, the time first.

- 21:20 **0a: subjects shown.** The inspector carries a reading's subjects under the headline (the specific first, an
  inferred one in italics, then the broad, the readings' `themes`, now said "broad subjects"); the paper tags each
  story with two subjects and `?subject=` shows only those stories. `products/board/subjects.py` reads both shapes.
- 22:10 **0b, 0c: the subjects pass, a trial.** `registers/news/subjects.py`: a second call after the read, the
  specific subjects with a kind (event, technology, product or work, law or policy, issue, programme or project,
  field) and the article's own words; the gate drops a subject whose words are not in the text and marks it inferred
  when its name's stems are not (decision 6, 8). Run on 20 gold articles of tranche 7 and Arthur's two examples (s1):
  both examples now carry theirs (3D-printed firearms; the 2022 Seoul Halloween crowd crush, inferred from "the
  Itaewon disaster"; Call of Duty). Waits on Arthur: the set `news-subjects-s1` in the review tab. Not in the live read.
- 05:15 **1: the name pass over news.** `pub.news_read_text` (the read articles' text, keyed by its sha256) and the
  lane `news` in links.sightings; job qv4-sightings-news after each news-read row and after the forms. Sample: 2,000
  articles, 23,246 sightings, 6.9 s. Found: junk forms the registers file as people ("of the" from court party
  lines: 5,351 of the sample's sightings; "in their", "South Island", "young people"), in every lane, not news alone:
  waits on Arthur (rebuilding the forms rescans every lane).
- 05:15 **2: article to record.** `links/news.py`: each read article's people and organisations keyed as the
  registers' rows are, tied to the register entities (pub.groups) of that key and kind: one group tied, several
  possible (decision 1); with each article's subjects and form. 33,628 readings in 24 s: 269,288 names, 42,073 tied,
  31,639 possible. Job qv4-links-news after the news pass. Found: many MPs are possible, not tied (Shane Jones, David
  Seymour, Chris Hipkins: a second small group of the same name, a LINZ owner or a split candidate return); an
  organisation matched by name alone can be a namesake ("White House" to The White House Incorporated).
- 05:45 **3 to 6: the feeds tab.** `products/board/feeds.py`, /feeds: find an entity the read news ties to, make a
  feed (broad: every relation, its subjects, every type, source and form), narrow it in the panel beside the
  stories (relations; subjects on or off, another name for a subject, a typed subject that catches its other forms;
  types, the six not joined yet shown off; sources; forms; withdraw). Newest first; each story says why it is there
  (named, central, in a role, connected: who and how, subject: which). Possible ties kept out and listed under the
  stories (decision 1). Feeds are lines in `<live>/board/feeds.jsonl`, the newest a feed's own, nothing erased.
  Connected (6): one step through the NZBN in a director's, shareholder's or officer's row key (companies,
  societies); charities' officer rows carry no charity number, so charities are not connected yet. Suggested
  subjects: in 5% of the entity's own articles and 8 times as often as in the read news; one that would bring in more
  than three times the feed's own articles starts unticked. Fonterra: dairy, dairy industry, commodities, banking,
  trade on, agriculture off; 1,023 stories matched, 0.5 s. Chlöe Swarbrick: polling; 679 matched.
- 05:55 **Measured, not applied: a political office settles a possible tie.** Of 30,458 possible people in the read
  articles, 3,618 have exactly one politician among their candidates, and in 2,197 of those the article's own roles
  give them a political office (minister, MP, leader, spokesperson, whip, Speaker, mayor, councillor): Simeon Brown
  229, Marama Davidson 224, Simon Watts 182, Barbara Edmonds 146, Todd McClay 142, Mark Mitchell 98. It would be a
  new links rule (method: twenty pairs, Arthur rules). Shane Jones and David Seymour are not settled by it: more than
  one of their candidates is a politician (split groups of one MP).
- 27 Nov, morning **The switch (Arthur: "lets make the switch then drip feed the already read articles in").** Reader
  `registers.news.read 6`, profile news-article version 2: a fourth pass, the subjects, gated as it lands. The ~36,000
  articles read before it take the subjects pass alone (reader `registers.news.subjects 1`, its own reading, recorded
  in news_private.subjects_done): job qv4-news-subjects, a row of 8,000 a night at 02:00, before the corpus read
  while it lasts. The inspector, the paper and links.news read either shape.
- 27 Nov **Arthur's reviews read.** Name forms list 1: 52 judged (14 junk, 38 closer look); office rule 20 of 20 yes;
  subjects s1 15 of 22 wrong. Rulings A–G on the closer-look classes (all yes; G junk; F places and languages out):
  - A: `keys.names.GOV_WORDS` (Crown bodies, courts, tribunals, iwi and rūnanga are organisations); the capture of the
    public sector's own lists asked of the provider (estate-public-sector-organisations@2026-11-27; legal position
    docs/legal/positions/public-sector-organisations.md, draft).
  - B: kind "office" (`keys.names.is_office`; links.rows): "Minister of Health", "the Attorney-General"; an office
    before a name is the person's title. Resolving an office to its holder on a date is next.
  - C: the parties register's names and their short forms are body rows (links.rows party_names); joining a party's
    several names into one entity is next.
  - D: an honorific is never part of a form filed whole. E: a form's kind is its rows' majority, not the first row's.
    F: a LINZ place name or a place abroad is no form unless a register that files people by name parts gives it.
    G and every junk answer: links/forms_judged.json (`python -m links.forms_review absorb`), read by the form build.
  - Measured on 10.6 M register rows: 10,497 person rows become offices, 9,768 organisations, 1,157 organisations offices.
- 27 Nov **Subjects s2** (prompt from Arthur's notes; micro events never subjects) on the same 22: review set
  news-subjects-s2. qv4-news-subjects held until s2 passes. **Offices pass** (registers.news.offices, a trial): review
  set news-offices-o1, the twenty office-rule articles.
- 27 Nov 18:13 **Rebuild done** (links build row 7311, forms 7332, news ties 7342): forms 4,502,997 person, 313,596
  organisation, 250 office, 299 estate; party-name@1 94 links; political-office@1 settled 5,014 news ties, passed over
  21,655. Entities still person/organisation/estate (Arthur's widen.py not yet run). 70 person forms kept a title the
  Companies Office files into the middle names: fixed in forms_of, takes effect at the next form build.
- 27 Nov evening, name-forms-1 against the rebuilt forms: of 1,500, 85 gone (14 judged junk), 183 changed kind, 1,194
  unanswered and unchanged. Rulings A and F reached less than they should: LINZ's region column holds no regions and its
  district column is a list, so Hawke's Bay, the West Coast, Tāmaki Makaurau were no place (REGIONS added, districts
  split); Te Puni Kōkiri, the SFO, the Parliamentary Service, the Defence Force, Civil Defence added to GOV_WORDS; a title
  glued by a stop ("Mrs.chandanie"). "hon trevor mallard", "dr michael cullen": current code gives no such form from any
  row; the next form build shows whether 7332 ran on older code.
- 27 Nov evening **Rule I** (Arthur: yes): an organisation form of company words and small words only is no form
  (COMPANY_WORDS; 59 forms today; the company's register row stays). **H** asked back: how the phrases came to be people.
  Found: links.rows recomputes every row's kind from the name (keys.names.name_kind, person unless an organisation word),
  ignoring a register's own kind: 41,788 diary attendees the diary reader called organisations are people in links.rows
  ("Family Violence", "RNZ", "Checkpoint"); and the court caption reader's 35,791 low-confidence parties are taken whole
  ("AND SOUTHLAND DISTRICT HEALTH", "OF AOTEAROA").
