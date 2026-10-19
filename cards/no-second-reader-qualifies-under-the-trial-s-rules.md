# No second reader qualifies under the trial's rules
kind: finding
state: open
use-case: Follow the Money (step 3.8: the second reader; the trial's resumption after the plan, ruling 60)
session: trial
opened: 2026-10-19

The plan's rule (3.8): the second reader is the best model from another
family with zero inventions, and a challenger replaces the incumbent only
with zero invented-text and loop failures and a better score on amounts.
Pass two was halted part-run under ruling 60, and on the pages each
challenger shares with the incumbent none reaches either bar:

| Reader (pages shared with GLM-OCR at 200 dpi) | Loop pages, challenger / GLM-OCR | Runaways of 100+ repeats | Invented pages | Exact amounts on complete keys |
| --- | --- | --- | --- | --- |
| OvisOCR2 Q8_0 (2,327 of 2,698) | 68 / 27 | 18 / 8 | 68 (19 on complete keys) / 1 | 128 / 123 of 142 |
| Infinity-Parser2-Pro Q4_K_M (445) | 24 / 9 | 5 / 1 | 12 (5 on complete keys) / 1 | 33 / 28 of 33 |
| Chandra OCR 2 Q8_0 (191) | 17 / 9 | 9 / 2 | 1 / 0 | 3 / 2 of 3 |

Every challenger reads amounts on the text keys at least as well as the
incumbent and runs away more often on the expense tables, where the
runaways are real (OvisOCR2 repeats one line 1,900 times on
`05da1deaca84` p4, 1,390 times on p1). Two parts of the count are the
measure's, not the model's, and are recorded so the resumption does not
repeat them: Infinity-Parser2-Pro prints each empty `$ 0.00` cell on a
line of its own, so a table of ten empty cells counts as a loop of ten
against a key that prints them inline (14 of its 24 loop pages are under
20 repeats); and the challengers' "inventions" on complete keys, inspected
on expense and financial-statement pages, are letterhead and form
instructions the text layer lacks and the incumbent does not read either
(`independent auditor's`, `bdo wellington audit limited`, the
Commission's bilingual name), plus Infinity's own ` ```markdown ` fence
(lesson `a-measure-judged-against-another-reading-counts-layout-as-failure`).

Under the rules as written GLM-OCR stays alone; the profiles' new versions
say so (`ocr.second_reader` null, `ocr.trial`). The Qwen family's two
small readers are the nearest to qualifying once the measures are
refined: OvisOCR2 for coverage (it read 86% of the set at 5.8 s a page)
and Infinity-Parser2-Pro for amounts (33 of 33). TeleOCR, the
top-scoring published challenger, was never served (card
`teleocr-needs-a-patched-server-the-scheduler-cannot-choose`).

Blocks: nothing now. Follow the Money reads with one reader, as the
frozen product does; a second reading of a disputed figure is a person's
(the reviewer), not a model's.

Fix (the trial's resumption, after the plan, ruling 60): the TeleOCR arm
once a profile can name its server; the rest of pass two (OvisOCR2's 371
pages, Chandra's 2,507, Infinity's 2,253, GLM-OCR at 300 dpi's 635); the
loop measure counting cells, not lines; the invention measure with the
page's letterhead in its bag; the rows pass; then this card closes with a
second reader named or the lack confirmed.
