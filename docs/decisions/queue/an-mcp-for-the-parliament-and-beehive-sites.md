# An MCP for the Parliament and Beehive sites (Arthur, parked)
default: no default (parked by Arthur: "let's wait, I'm too busy now")
blocks: nothing yet; touches template 4 (lobbying, step 6.2) and ruling 78
recommendation: none until Arthur answers the three questions below
raised: 2026-10-23 by Arthur, about 15:20 NZDT, in conversation with the status agent; recorded by the integrator

Arthur's words: "I want to add an MCP for the parliament and beehive sites",
then "let's wait, I'm too busy now". Nothing is built or scoped. Ruling 78
stands: Beehive and Hansard are not captured by the estate; the source for
them is Arthur's third-party one. Ruling 79 stands: no document reading by a
model until both boxes are up, which is what holds template 4.

Three questions decide what this is, asked by the status agent and not yet
answered:

1. Which MCP: ruling 78's third-party source (a server someone else runs for
   parliament.nz and beehive.govt.nz that we connect to), or one we build
   that reads the two sites live, which meets the Beehive wall that refused
   the diaries reader (a challenged read is a failed read, hard limit 6).
2. Who calls it: a Claude session, Arthur in Claude Desktop, or the estate's
   jobs and the lobbying template. Jobs and templates run on the boxes' own
   models (hard limit 10), so for them the answer is a register fed by the
   MCP, not the MCP itself.
3. What it answers: ministers' diaries and press releases (Beehive); Hansard,
   bills, questions, members, select committees (Parliament); or a subset.

When Arthur returns to it: his answers, a one-page legal position for the
source class before any product shows it (ruling 61), and where it sits
against template 4.
update: 2026-10-26 about 10:10, the explainer agent, given read-only access by Arthur, cloned the ingest repository (its name and address struck under ruling 92; head dabc5e6, 29 files) into the integrator's scratch folder and reported: a beehive.govt.nz scraper (56,431 URLs inventoried; topics and quotes extracted by a cloud model), a parliament.nz scraper (sitemap diff, Hansard PDFs, written questions, debates, bills; a Wayback harvest of legacy URLs) and an MCP server (port 8646; corpora, search, get, recent, measure) over their jsonl output, all running on a separate box, not node1 or node2; no credential committed. Not verified by the integrator; nothing from it has been run. Points for the decision: (a) its corpus text has already passed through a cloud model on that box, outside the estate, so the estate may consume the output but no estate job may call its extraction (hard limit 10); (b) its parliament capture works through a challenge with a residential proxy pool, which hard limit 6 forbids the estate's own capture, so the estate would take these records only as a third-party source (ruling 78) with a legal position page before any product shows them (ruling 61); (c) template 4's diaries would come from its Beehive corpus, which still waits on ruling 79. The three questions above stand.

update: 2026-10-26 16:10, ruling 94: Arthur set the MCP up as a source on node2 (tunnel unit `qv4-mcp-tunnel`, registered for Claude Code in the project directory); the three questions are answered by the ruling (a third-party source lane, no estate call of its extraction, a legal position before any product). This item closes when the lane is briefed; the node1 setup is owed at its return.
