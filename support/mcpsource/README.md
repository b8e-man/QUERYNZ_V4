# support/mcpsource — the ingest MCP as a source (ruling 96)

The client for the `query-nz-ingest` MCP reached through the tunnel unit
`qv4-mcp-tunnel` (ruling 94), a cursor per corpus, and the job
`qv4-mcp-pull` that polls `corpora` and pulls `records` from each cursor,
landing every record whole as a captured document (ruling 96). Built by
`mcp-1`.
