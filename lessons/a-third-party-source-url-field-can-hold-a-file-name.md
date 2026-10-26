A field named `source_url` is not an address until every value is: the MCP's diary records serve the Beehive PDF's address for 2,441 releases and only its file name for 119, so publish the address where there is one, the file name beside it always, and never build an address from a name.
area: mcpsource, ministers_diaries, citations, third-party sources, registers
paid-for-by: 2026-10-27, diaries-2, the parliament-diaries corpus

The provider read the diary PDFs off-estate; its `source_url` is
`https://www.beehive.govt.nz/sites/default/files/<YYYY-MM>/<file>.pdf` on
197,465 entries and a bare `Hon <Name> - <Month YYYY>.pdf` on 10,999 (the
newer releases, 2026). The shape check in support/mcpsource sees a string and
passes both. A citation column filled from it would have carried a file name
as a link. The file name's month can also be a span ("October 2017-December
2018"): take a month from a name only when it names exactly one.

How to apply: profile the citation field's shapes over the whole corpus
before naming the column; keep the address NULL where none was served and
carry the file name in its own column on every published row.
