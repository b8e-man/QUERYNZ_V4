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
