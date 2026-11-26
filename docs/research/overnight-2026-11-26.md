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
