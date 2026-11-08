# The plan (9 November 2026)

## Where we are

Since 5 November the MCP is meant to do all the collecting from websites. Our own machines keep only the
official data services (Companies Office, LINZ, insolvency and so on).

The move is half done:

- **6 sources** come from the MCP already: Parliament, Hansard, Beehive, ministers' diaries, the courts and
  government tenders.
- **9 sources:** the MCP collects them, and our machines have stopped. Their new material can't reach us
  yet because of a fault on the MCP's side (request 1 to the MCP).
- **5 sources:** the MCP holds only an old copy, so our machines still collect them.
- **2 sources** (donations and candidate returns): both collect them. Ours comes from the old system.
- **9 sources:** loaded once; nothing keeps them up to date.
- **10 sources:** official data services that stay on our machines, all working.

## Part 1: finish the move to the MCP

| Step | Who | What |
| --- | --- | --- |
| 1 | Arthur | Send `docs/letters/mcp-provider-2026-11-09.md` to the MCP provider |
| 2 | MCP | Fix file downloads |
| 3 | Claude | Fetch everything that waited; check each of the 9 registers updates |
| 4 | Claude | Switch the other 8 of those 9 to read from the MCP (FMA already does), testing each |
| 5 | Claude | Make the board show a gap when the MCP is missing something, not a green light |
| 6 | MCP | Start the 5 old-copy sources again, and take on the 9 nobody collects |
| 7 | Claude | As each comes in fresh, stop our machines collecting it and switch its register over |
| 8 | Arthur | Decide donations and candidate returns (they also feed the frozen site) |

When this is done, every website source comes from the MCP. Our machines only read, link and check.

## Part 2: decide in the planning session

1. **What the next stage is for.** Which uses of the data come first. That decides which sources and gaps
   matter most.
2. **The new site.** It rebuilds cleanly every morning now. What has to be true before it replaces the
   frozen one?
3. **The old system.** What still depends on it (donations, candidate returns, the frozen site, the Papers
   Past archive) and when it can be switched off.
4. **The gaps in Parliament, Hansard and ministers' diaries.** Request 5 asks the MCP to fill them all.
   Which matter enough to chase?
5. **Our own checks.** Some test groups have been failing for days. Fix them, or retire the ones that no
   longer protect anything.
