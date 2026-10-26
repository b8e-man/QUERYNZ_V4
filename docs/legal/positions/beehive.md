# The Beehive's releases, speeches and features, through the ingest MCP (draft position, ruling 61)

hosts: beehive.govt.nz

Class: the New Zealand Government's official website, www.beehive.govt.nz
(ministers' press releases, speeches and features, 1999 on), as records of
the `beehive` corpus of the ingest MCP `query-nz-ingest` run by Arthur's
provider (rulings 78, 94, 96). Lane: `registers/beehive`; the pull is
`support/mcpsource`. Draft, held in the lane's folder because the fence keeps
a build session out of `docs/legal/positions/`; the integrator moves it there.
Written 26 October 2026 by mcp-1.

**Finding: open, and lawful to copy and show with attribution, on the Crown
licence the site states (to be read by the lawyer from the site's own
copyright page: the estate may not fetch it, ruling 78). The capture was not
the estate's. The provider's topics and quotes are a third party's model
output and are shown only as theirs.**

**How the material reached us.** The estate fetched nothing from
beehive.govt.nz (ruling 78: "forget about capturing the beehive … I have a 3rd
party source"). Arthur's provider captured the pages on its own box, outside
the estate, and serves them as structured records through the MCP, reached
over an SSH tunnel to the provider's VPS (`qv4-mcp-tunnel`). The estate's pull
asks that server for records (one request at a time, 200 a page) and lands
each whole by hash. The provider also ran its own model over the pages to
make two fields, `topics` and `quotes`: a cloud model the provider called from
its own box, outside the estate. Since the server's redeploy of 26 October each
record names it in an `annotation` block (`fields`: topics and quotes, never
another; `generator`: `deepseek/deepseek-v4-flash` on most records,
`z-ai/glm-5.3-flash` and `deepseek/deepseek-v4.1-flash` on a few). Hard limit 10
is met: no text of ours goes to any model; we only receive what the provider
made, and the lane keeps it apart, marked model-made with its generator.

1. **Is the page open?** The Beehive's pages are public and need no login. Before
   21 October the estate's own reader of the ministers' diaries was
   refused by the site's wall (the card `the-beehive-s-wall-refuses-the-
   diaries-reader`, closed by ruling 78 with no request made): the estate
   neither passed it nor asked to. How the provider reached the pages is the
   provider's; the estate did not get past any lock, challenge or block (hard
   limit 6). For the lawyer: whether material a third party captured past a
   wall the estate itself met may be held on the provider's word that it was
   open to them.
2. **Is storing it lawful copying?** The site is the Government's, its
   content Crown copyright. New Zealand government sites publish under
   NZGOAL, mostly as Creative Commons Attribution 4.0 International, which
   permits copying, adapting and commercial reuse with attribution; the
   Beehive's own statement is to be read from its copyright page by the
   lawyer or Arthur (the estate may not fetch it). Releases and speeches are
   not among the works with no copyright under the Copyright Act 1994, s 27
   (that covers Bills, Acts, parliamentary debates and the like), so the lane
   relies on the licence. Every row carries the page's address as its
   citation, which is the attribution. The provider's `topics` and `quotes`
   are its own work over Crown text; whether the provider claims rights in
   them is a question for the provider's terms.
3. **What terms did we accept?** None with the Beehive (the estate never
   visited it). With the provider, whatever Arthur agreed when he set up the
   MCP (ruling 94); its server says only "Consumers may ingest the full corpus
   via the `records` tool". Those terms, in writing, belong on this page
   before anything is sold.
4. **What does privacy law, or the statute, limit?** Releases name ministers,
   officials and members of the public in public roles, sometimes a person in
   a story (an award, a victim, a constituent). The Privacy Act 2020 applies to
   our holding: the body and text are kept in `beehive_private.texts` and never
   published; the views show the title, the date, the ministers and portfolios
   the site tags and the provider's annotation, each cited to the page. No
   address column exists (hard limit 15). The quotes' speakers are named as
   the provider's model named them, which may be wrong; they are never a link
   or a claim about a person (ruling 96; hard limit 14 for any new connection
   on the public site).

Crawl delay: not applicable (nothing fetched from the host). Floor for the
MCP: one request at a time, a pause of a second between pages, a call waited
for up to three minutes and retried after 30 s doubling to 10 minutes; the
nightly pull runs off-peak NZ time. Author: mcp-1 (Opus), 26 October 2026. A
lawyer reviews this page before anything is sold.
