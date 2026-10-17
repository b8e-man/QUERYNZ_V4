# support/profiles — the document profiles

`profiles.jsonl`: one line per profile version, from the old estate's
`data-layer/docreview/profiles.jsonl` (commit `29f0412a`), 45 lines, 22
profiles. The newest line per `slug` is the current version. **Added to,
never rewritten:** a new version is a new line with `version` one higher and
`at`/`by` filled; an old line is never edited. The document-profile contract
(step 1.9) says what the fields mean and how a version is added.

At the copy, thirteen occurrences of one donor's street address, quoted in
`tables` and `notes` as an example of a mis-read, were replaced with
`<a donor's street address>` (hard limit 15: no export carries one). Nothing
else was changed.

**The corrections are not here.** `corrections.jsonl` (390 corrections a
person or a check made to readings) quotes transcribed donor rows, street
addresses included, so it does not enter git. It is at
`/home/user/querynzv4-work/live/reference/corrections.jsonl` on node2,
untouched, until the document store (1.8, 1.10) gives it a home in a
`_private` schema.
