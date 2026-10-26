# The ingest MCP's first pull is a bulk load before 7 November
default: it goes ahead. mcp-1's first pull landed every record of all six corpora into the document store and the sample database; the integrator carries it into the live database once (`qv4-mcp-adopt`, about 740,000 documents re-landed from the store, no request to the MCP), then the nightly pull takes only arrivals. Striking it is a setting: run `qv4-mcp-pull` with `--corpus` naming only the small corpora until after the election.
blocks: nothing; the default applies.
recommendation: the default. The plan's "bulk loading stays small" (core, "Shared things on the boxes") was written for the Papers Past ingest; this load is rows of a few hundred bytes each in `docs` and `mcpsource`, and its write-ahead log was measured (see mcp-1's merge request) at a small share of the weekly budget. Ruling 96 ("I want everything … I dont care what comes in first") asks for all of it.
raised: 2026-10-26 by mcp-1
