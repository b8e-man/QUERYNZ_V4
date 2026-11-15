# Golden sample, tranche 1: what the trial showed (15 November 2026)

32 articles from the old copy's last 60 days: 20 spread over ten sites, 12 chosen for the hard cases. Labelled by
hand to SCHEMA.md (1,383 spans, every one held to its text by check.py), then read once by the boxes' text model
(qwen4exp on node2's Radiance, temperature 0, one call per article, about 20 seconds each, all 32 parsed). Scored by
`trial.py score`; outputs in /home/user/querynzv4-work/live/news-trial/tranche-1/.

## The numbers

| Measure | Result |
| --- | --- |
| People found | 95% |
| Entities found (all kinds) | 93% |
| Spans the model printed that are not in the text | 0% of 954 |
| Roles it bound to an organisation that the labels bind the same way | 75% (55 of 73) |
| Quotes found | 77% (direct ones nearly all; the misses are indirect) |
| Speaker right, of quotes found | 92% |
| Allegations kept as alleged (of 5) | 3 found and kept; 2 not extracted at all; none turned into fact |
| Sentiment agreeing with the labels, where both have one | 100% of 34 |
| Article type right | 28 of 32 |

## What the 18 role bindings that disagree are

- **One real and harmful error.** In the Ascend Works column the model made Alastair Paton the
  "shareholder-appointed liquidator" of his own collapsed firm. The liquidator is someone else, unnamed. This is
  exactly the false fact the plan fears. Defence: a role must sit in the same clause as the person's name.
- **Filling in from outside the text (4).** It gave Nicola Willis National, the Niue ministers Niue, and the
  detective NZ Police, where the text does not print the binding. These are true in the world but not in the
  article. Defence: the prompt's rule needs a check after the read, not only a sentence in the prompt.
- **A place as an organisation (2).** It bound "Kāpiti Coast builder" to Kāpiti Coast as if it were an employer.
  Defence: `of` must be an organisation or government, never a place.
- **Relations put in roles (6).** It recorded "mother", "father", "lawyer" and "wife" as roles *of* a person, where
  the labels put them in relations. This is the schema's ambiguity, not an error of fact. Defence: a role's `of` is
  never a person; anything person-to-person is a relation.
- **The labels or the scorer, not the model (5).** Its entity names sometimes carry the role ("Waikato police
  Superintendent Scott Gemmell"), so the scorer failed to match them. It also bound judges to their courts where the
  text places them in the court ("In Manukau District Court this week"). That binding is defensible, and the
  labels left it unbound.

## Other findings

- **Indirect quotes are the main gap.** Paraphrase ("X said that …") is missed far more often than quotation marks.
  This matches the research corpora. Reading quotes in a second, separate pass is the first thing to try.
- **Its kind is not held to the list.** It answered "analysis" (not in the list) and called a review, a market wrap
  and a feature "news". The next run constrains every enum with a JSON schema; the server supports grammar.
- **The text itself has faults the reader must survive:**
  - lost paragraph breaks;
  - site boilerplate (Scoop, Newsroom);
  - photo captions mid-text;
  - a truncated opening;
  - a list dropped from the copy;
  - a misspelt byline;
  - a paywall stub;
  - an advertorial dressed as news.

  These belong to the prepare step, with one profile per site family.
- **What it got right that the plan feared:**
  - Hugo Charitable Trust read as an organisation, not a person called Hugo;
  - Meridian Partners kept apart from Meridian;
  - "a warehouse" kept as the word;
  - The Warehouse Group as a company;
  - every unnamed victim left unnamed;
  - no invented span.

## Next

1. Arthur labels a handful of these articles himself, and checks them against mine.
2. Second run, with the enum schema, the role and relation rules above as checks after the read, and indirect
   quotes in their own pass. It is scored against the same labels.
3. Tranche 2, with more of the kinds that scored worst: opinion, market wraps, court stories, live blogs.

## Run 2 (same day): schema, quotes in their own pass, checks after the read

Changes from tranche 1:
- every enum is held by a JSON schema, which the server enforces;
- the role, name and allegation rules from tranche 1 are written into the prompt;
- quotes are read in a second call, given the first call's entities;
- `check` runs after the read: a role whose `of` is a person moves to relations, a role bound to a place is unbound,
  and so is a binding whose role, person and organisation are not printed in one sentence.

The scorer now also matches a person whose got name carries the role. Rescoring run 1 with it moves entities to 95%,
role binding to 77% and speaker to 95%.

| Measure | Run 1 | Run 2 |
| --- | --- | --- |
| People found | 95% | 93% |
| Spans not in text | 0% | 1% (11 of about 1,300) |
| Roles bound right | 77% | 88% (45 of 51) |
| Quotes found | 77% | 96% |
| Speaker right | 95% | 93% |
| Allegations kept as alleged | 3 of 5 | 5 of 5 |
| Sentiment agree | 100% | 94% |
| Type right | 28 of 32 | 27 of 32 |
| Seconds per article | about 20 | about 32 (two calls) |

- **The Paton error is gone**, unbound by the prompt rule.
- **Spans not in text:**
  - nine indirect quotes begin with a "that" the article does not print, and the next run strips it;
  - "the offender" and "France" were printed by the model and are not in the text.
- **Six bindings the labels do not hold remain:**
  - the detective bound to Police, and Willis to National. The one-sentence check passes both, because the name
    and the organisation share a sentence that the lost paragraph breaks have run together;
  - "board chair" of "board";
  - an associate professor bound to her school. This one is defensible: it may be the labels' gap;
  - two film credits ("Produced by") bound to the film.
- **124 of the 338 quotes it found match no labelled quote.** Most of the ones sampled are real indirect or direct
  quotes that my labels missed (the Naida Glavish memoir feature most of all). The labels are short on quotes, so
  quote precision cannot be scored until the labels are completed. Arthur's labelling will measure how much is
  missing.
- **Article type is still weak.** It reads a review, a feature, a market wrap and an advertorial as other kinds, and
  a paywall stub as opinion. Type may need its own small call, or a rule taken from the site and the URL, which
  often carry it.

The pack for Arthur: /home/user/querynzv4-work/notes/news-gold-pack/ (`pack.py`). It holds three articles to label
himself and three of mine to check.
