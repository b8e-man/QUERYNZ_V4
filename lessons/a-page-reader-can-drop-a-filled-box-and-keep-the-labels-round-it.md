A page reader can drop a filled box whole and keep the labels round it: find what is missing before tuning the parser, and fall back to the typed text layer only on pages with no full-page picture.
area: reading documents, EC disclosures, declaration page, OCR, page reader, text layer, scans
paid-for-by: 2026-10-20, disclosures session 3, step 4.1

Of the 50 large-donation declarations whose total was not read, the
stored GLM-OCR reading of 49 held the form's labels and dates but no
"Total amount" line at all. Typed and handwritten boxes were dropped
alike (31 typed, 18 handwritten, 1 truly empty). The fiftieth was a parser
fault: a bare "$20,000" in the box matched the boilerplate filter, which
was there for the form's printed "$20,000" threshold. 23 of the 49 carried
the figure in the PDF's own text layer, and that layer gave the box's
figure on 126 of 126 typed pages. On pages under a full-page picture
(scanners' PDFs with their own OCR layer) it gave junk 6 times in 24
("$9", "$50"). Tell the two kinds of page apart with `pdfimages -list`
(an image as wide as the page), never by producer name. And an empty box
is not the first figure of the grid of gifts under it.
