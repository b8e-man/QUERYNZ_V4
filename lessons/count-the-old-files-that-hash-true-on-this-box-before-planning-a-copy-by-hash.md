Before planning to copy the old estate's documents by hash, count the files that hash true on this box: 1,159 council minutes were stripped text with no bytes, and 351 PDFs sat on the box that was down.
area: capture, old-estate, docstore, council_minutes

Why: the brief said the old estate holds about 1,141 InfoCouncil documents to copy by hash. The old news database
lists 351 of them in `documents` with a sha256 and a path, and keeps 1,159 more only as `articles.text_content`
(the old capture stripped the tags and threw the page away). On node2 none of the 351 paths exists: the files are
on node1, which was out of service. So "copy, don't fetch" held for 347 (recorded with the old hash, never fetched,
copied when the box returns) and was impossible for the rest, which had to be fetched.

How to apply: before writing a lane's case 1, run three counts against the old listing: rows with a sha256 and a
path, paths that exist here, files whose bytes hash to the listed sha256. Plan the copy on the third number; record
the gap as a card naming the box that holds the rest.
