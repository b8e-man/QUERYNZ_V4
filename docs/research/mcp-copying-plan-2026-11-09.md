# Copying the handed-over sources from the MCP: the plan (9 November 2026)

On 5 November every website crawl moved to the ingest MCP's provider. On 9 November the boxes stopped
crawling the nine sources the MCP was found to be collecting itself. This plan is how those registers keep
updating from the MCP instead.

## How it works

1. **Copy.** Every six hours `qv4-mcp-pull` copies each source's records from the MCP (`estate-<source>`)
   and the page or file each record points at into our store. A file whose exact bytes we already hold
   costs no request.
2. **Replay.** Each source's own collector runs as before, but every page it would have fetched from the
   web is answered with the newest copy the MCP holds of that address (`support/mcpsource/replay.py`).
   Its bookkeeping and the register it feeds update exactly as they did. Nothing is fetched from the web.

## Where it stands

| Source | Copied | Replay wired | Proven |
| --- | --- | --- | --- |
| FMA | yes | yes (`--from-mcp`, nightly) | yes: 801 of the live register's 804 entries; the other 3 are a take-down history a fresh replay cannot know and two cases on pages the MCP will not yet hand over |
| WorkSafe | yes | next | |
| Commerce Commission | yes | next | |
| Councillors' interests | yes | next | |
| Council minutes | yes | next | |
| Building practitioners (decisions) | yes | next | |
| Building practitioners (the register) | yes | needs its own adapter | |
| Local elections | yes | needs its own adapter | |
| Courts: JDO and ERA copies | yes | needs its own adapter | |

## Blocked on the provider

**The MCP's `download` tool fails on every `estate-*` record.** Each record's `file` field holds a doubled
path, for example `/opt/data/querynz-estate/sources/fma/opt/data/querynz-estate/store/9b/9b02…`. The
download errors on all nine corpora tried; the `courts` corpus downloads cleanly. Until it is fixed we
receive only the pages whose bytes we already held. For FMA that is 913 of 1,072; the 159 new ones are
logged and taken once it works. Arthur to pass to the provider.

## The steps, in order

1. Provider fixes `download` for the `estate-*` corpora. Then: `python -m support.mcpsource --retry-caught`.
2. Wire and prove the five sources whose collectors take an opener, one at a time, like FMA: a full pass
   replayed into a scratch ledger, the register built from it and compared with the live one.
3. Write adapters for the three that fetch differently (the building practitioners register, local
   elections, the courts copies), then prove them the same way.
4. Give each source's board light its MCP corpus, so a file the MCP will not hand over shows as a gap
   rather than a green light.
5. Ask the provider to resume collecting the five sources the MCP holds only as the 5 November copy:
   charities, the Real Estate Authority, the Tenancy Tribunal (its host is held), the iwi directory and
   settlement commitments. When each is fresh, stop the boxes and repeat steps 2 to 4.
6. Disclosures and candidate returns: the MCP collects both, but our copies come from the old estate's
   Electoral Commission capture, which also feeds the frozen site. Arthur's decision (hard limit 22).
