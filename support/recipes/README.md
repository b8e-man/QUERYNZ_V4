# support/recipes — how each kind of document is read, recorded against what it produces

Arthur, 26 November 2026: each document profile picks its best reader configuration from measured evidence; every
row is traceable to its full configuration; a switch is proposed to Arthur, never applied by itself.

Five append-only ledgers, each line keyed by a hash of what it records, so an id never changes its meaning:

| Ledger | Records | Id | Tranche |
| --- | --- | --- | --- |
| Servings (`<live>/recipes/servings.jsonl`) | How a model is served: the installed units (cards, concurrency, context, thinking), the image by id, the weights by sha256 (`weights.jsonl`) | `serving_id` | 1, built |
| Document profiles (`support/profiles/profiles.jsonl`) | How to recognise a document, and its candidate and chosen recipes | slug@version | exists; candidates in 2 |
| Recipes | How one document profile is read: the model view, passes, prompts by hash, request settings, gates version, reader code | `recipe_id` | 2 |
| Golden sets | Frozen, versioned answers: Arthur's judgments with the measures that score them | set@version | 3 |
| Trials | A recipe on a serving against a golden set: the measures and the speed | trial id | 4 |

Then: a selector that proposes a recipe change to Arthur from the trials (5), and every other lane moved onto
recipes (6).

A reading carries `serving` (the id) beside `reader`, `model`, `settings`, `profile@version` and `commit`.
`serving.resolve(id)` returns what the id meant. `python -m support.recipes.serving show` prints this box's
standing servers and their ids.
