A third-party `source_url` is not an address until every value is: the diaries corpus serves a file name for 119 of 2,560 PDFs, so publish the address only where served, the file name always, and never build one.
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
