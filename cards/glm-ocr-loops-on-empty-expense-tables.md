# GLM-OCR loops on empty expense tables
kind: finding
state: open
use-case: Follow the Money (step 3.7, the loop measure; the incumbent's standing failure)
session: trial
opened: 2026-10-19

On candidate and party expense returns whose tables are mostly `$0.00`,
GLM-OCR (Q8_0, prompt `OCR`, temperature 0) runs away: pass one holds
seven pages with the same line repeated 650 to 1,324 times
(`02e7fb6587a3` p11, `095a6440cb3b` p10, `e1a76eede431` p12 and p14,
`789b35136533` p9, `a5bf53fd060c` p8 and p13) and one page
(`2f966d882745` p8) where it loops sideways, 1,446 amount tokens on one
line, which the line rule missed until a within-line rule was added
(`score.LINE_LOOP`, twelve of the same token in a row). The old estate's
cached readings of the same page images carry the same loops (old_equal
true on six of the seven), so this is the model's own behaviour,
reproduced, not the harness. Nineteen further pages repeat a short line
3 to 37 times; whether those are loops or genuinely repeated rows is
decided against the other readers in pass two.

Under the plan's rule each such page fails; a part on it is not read. Of
the 2,698 pages of pass one, 28 fail the loop rule (20 scan, 7 mixed, 1
text page). The pages are expense returns, not donation returns, so the
product's donor rows are not affected; the expense figures on those
pages are.

Blocks: nothing. The challengers are judged on the same pages; a reader
with zero loop failures and no inventions qualifies to replace the
incumbent (3.8). If none does, this card becomes a known limit of the
incumbent on expense returns.
