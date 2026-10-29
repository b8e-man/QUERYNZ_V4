# support/mcpsource — the ingest MCP as a source (rulings 96, 126)

The client for the `query-nz-ingest` MCP reached through the tunnel unit
`qv4-mcp-tunnel` (ruling 94), a cursor per corpus, and the job
`qv4-mcp-pull` that polls `corpora` and pulls `records` from each cursor,
landing every record whole as a captured document (ruling 96), then fetches
every file a record points at through the `download` tool and lands it by
hash under the record's url, refusing bytes whose hash is not the record's
(ruling 126; the courts corpus today). The spec is `spec.md`; the module's
docstring says how a record, and a file, becomes a document.

    python -m support.mcpsource --database querynz_v4_sample --schema scratch_<session>_pull --runs <scratch>/runs.jsonl
    python -m support.mcpsource --no-files      the records only, no metered download
