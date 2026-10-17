### Reading documents

| Piece | Where | Faults on record | Verdict |
| --- | --- | --- | --- |
| Page reader | The `querynz-vision-ocr` job; GLM-OCR | The only one, with nothing behind it. Killed for memory once; capped at 6 GB. It had never actually run until 24 September because of a code bug | Take. Step 3 gives it a second |
| Document reader and checks | `data-layer/docread` | One reader, so no automatic second opinion. 264 of 844 stored readings failed their own stated total. Tables of 6 to 20 rows passed 48% of the time. Table size predicts failure; text or scan does not | Take the checks and the answer-set method |
| One reader contract | None | 11 text-extraction calls in 4 shapes across 9 files | Build in step 1 |
| Profiles and corrections | `data-layer/docreview`, `profiles.jsonl` | A profile is pinned to the code both ways for one form only. 379 of 381 corrections are machine-agreed. 16 corrections reach no page | Take. The reader runs from the profile |
| Model client | `data-layer/modelgate/modelgate/client.py` | For most jobs it recorded a wrong model and carried on | Take, with refusal on for every lane |
| Geometric table reader | `data-layer/docread/retired/geometry.py` | Retired 25 September; needs a reader that returns word positions | A possible second opinion on tables |
| Row-pairing check | `ops/party_return_rows_pairing.py` | Experimental | Refuses a table whose columns have drifted; worth wiring into scoring |

