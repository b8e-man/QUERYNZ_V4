Check delivered bytes against the record's own hash, never the server's "matches" flag or its meta block, which normalises what the record keeps (the MCP's download meta drops a content type's charset).
area: mcpsource, capture, document store, hashes
paid-for-by: 2026-10-30, fix-support-mcpsource-2 (ruling 126)

The `download` tool answers with a meta block (`delivered_sha256`,
`captured_sha256`, `sha256_matches_capture`, `content_type`) and the file as
an embedded base64 resource. The meta is the server's account of itself:
its content type is the main type alone (`text/html` for a record that says
`text/html; charset=utf-8`), and its match flag compares two of its own
figures. The live shape test first held the meta's content type equal to
the record's and failed on the first case page.

How to apply: hash the bytes you received and compare them with the hash
the record carried when it was landed; land under the record's content
type; read the meta for provenance (the capture's fetch time) and shape
only. Compare content types by main type where a server's wording may
differ from the record's.
