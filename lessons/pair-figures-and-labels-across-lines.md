The layout tool parts a figure from its label on the declaration page (the total sits ABOVE its label): pair labels and lone figures in order, take lone figures only from the amount column, and let total = A+C+D+F+G catch a mispairing.
area: reading documents, EC party returns, text layer, declaration page
paid-for-by: 2026-10-18, founding session, 1.11

The carried parser (`support.docread.parse`) was tuned on a page reader's
output, where label and figure share a line; on `pdftotext -layout` text it
found the declared total in 0 of 22 returns. Pairing first-in first-out
across lines, with a column rule for lone figures, read 22 of 22, each
reconciled with its own parts and each equal to the frozen site's figure.
A figure that stands alone BEFORE the first part label is the step-2 cell
(`NIL`, or the total typed there), not a part's figure. The reader is
`registers/party_returns/declaration.py`; its tests hold the shapes.
