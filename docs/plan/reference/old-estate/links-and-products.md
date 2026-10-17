### Links and products

| Piece | Where | Faults on record | Verdict |
| --- | --- | --- | --- |
| Donor matcher | `registers/donor_anchors.py` | Hand-set weights. One rule accepted by a rounding margin. A withdrawn match once supported new ones | Take the ledger and the two rules, not the weights |
| Director folds and the watch | `registers/roster_folds.py`, `folds.py` | Built for donor and MP names only; the whole 1.19 million director rows were never done. 857 of 5,314 folds were contested at first run | Rebuild over the whole register |
| Ordered resolver | `registers/person_identity.py` | None documented | Take as is |
| Verdicts and review threads | `registers/review_verdicts.py`, `review_comments.py` | The only verdict is "hold", tied to a weights version. The comment route once took the author's name from the caller | Take as decisions; re-key to rule and evidence |
| Old answer set | `data-layer/candidate_register/truthset` | 207 hand labels of names in press text, not register rows | Take the method only |
| Company views | In `registers` | An ended role is dated to the day the file was imported | Rebuild with real dates |
| Ownership notes | `registers/vehicles.py`, `exposure.py` | Exposure has had no reader since 30 September | Take the rule: ownership is a note, never summed |
| Land title owners | `registers/linz_title_owners.py` | Individuals held with no matching; takedown service parked | Step 5, takedown first |
| Sealed address store | `registers/sealed.py` | Built and not yet fired | Arthur fires it before 18 November |
| Follow the Money app | `data-layer/pi` | Imports the inside of `registers`; the donor list cut before folding | The pattern for a product; rebuild on the shape |
| Release pipeline | `ops/pi_release.py`, `pi_snapshot.py`, `pi_cloudflare.py` | Every gate reads our own output | Move without its deploy step and without its ties to the frozen publisher (step 4.4); add one outside check |
| Flags and rule sets | `data-layer/flags` | Seven person rules and four company rules exist; there is no hostile test set | Take the idea |
| Watchlists and feed | In `query` | Acceptance check never built | Take with care |
| Search service | `data-layer/corpus_search`; `data-layer/query/query/semantic.py`; `ops/embed_articles.py`, `ops/build_embed_index.py` | Keyword index reads 1,500 characters. The meaning index is built whole in memory: 33 to 38 GB for 6.4 million articles on a 62 GB box | Take the tools; rebuild both indexes |
| Research agent, gap miner | `data-layer/research` | Its web fetch is the strongest injection channel in the estate and is not on the fetch gate | Internal use only |

