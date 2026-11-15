# The golden labels: one JSON file per article

`labels/<article id>.json`, typed by a person (a session or Arthur). These files cannot be regenerated and are
never deleted. Every text value is **verbatim** from the article as `sample.py show` prints it. The scorer finds the
offsets; nobody types them. A street address shows as `[street address]` and is labelled as such, never restored.

```json
{
  "id": "…", "text_sha256": "…", "labelled_by": "session 40ea495e | arthur", "labelled_at": "2026-11-15",
  "article": {"type": "news | opinion | press_release | live_blog | review | feature | obituary | market_wrap | letter",
              "themes": ["IPTC Media Topic labels, broad to specific"], "dateline": "as printed or null",
              "wire_credit": "AP | Reuters | AAP | … or null"},
  "authors": [{"as_printed": "…", "kind": "person | staff | agency | organisation", "role_line": "… or null"}],
  "entities": {"e1": {"name": "the fullest form printed", "kind": "person | organisation | place | team |
                       government | brand | product | thing | work | event", "forms": ["every way it is printed"]}},
  "roles": [{"who": "e1", "role": "as printed", "of": "e2 or null", "tense": "current | former | acting | interim |
             incoming | designate", "bound_by": "apposition | possessive | premodifier | statement | unbound"}],
  "relations": [{"a": "e1", "says": "as printed", "b": "e2"}],
  "descriptors": [{"who": "e1", "text": "as printed (age, town, occupation)"}],
  "quotes": [{"text": "…", "form": "direct | partial | indirect | mixed", "speaker": "e1 or null",
              "speaker_as_printed": "…", "verb": "said | …", "channel": "interview | statement | court | social |
              earlier_article | release | unknown", "about": ["e2"]}],
  "events": [{"kind": "…", "who": [{"e": "e1", "part": "…"}], "when": "as printed or null", "where": "e3 or null",
              "modality": "happened | alleged | denied | planned | rumoured | possible"}],
  "numbers": [{"text": "as printed", "measures": "…", "of": "e2 or null"}],
  "sentiment": [{"toward": "e1", "from": "article | e4 (a quoted speaker) | own", "value": "negative | mixed |
                 neutral | positive", "evidence": "the words that carry it"}],
  "traps": ["the hard cases this article holds, in plain words"]
}
```

Rules:
- **One entity per real thing in this article.** "Mr Smith", "Smith" and "he" are all forms of e1. A pronoun is
  not listed among the forms; quotes that are attributed through one name the entity.
- **A role binds to an organisation only when the text binds it.** Otherwise `of` is null and `bound_by` is
  `unbound`.
- **Nothing from outside the article.** If the article does not say who "the chief executive" is, nobody does.
- **Things named after people** (Eden Park, Ryman Healthcare) are their own kind, never a person.
- **Captions are labelled as captions**, under `traps`, when the text carries them.
