# Parliament's written questions, bills, committee papers and archived pages, through the ingest MCP (draft position, ruling 61)

hosts: parliament.nz

Class: the New Zealand Parliament's website, www.parliament.nz, and the
Parliament API behind it (written questions with their replies, bills
current and historical, select committee calls for submissions and
reports, supplementary order papers), with parliament.nz pages from 2006 on
as the Internet Archive kept them, as records of seven corpora of the
ingest MCP `query-nz-ingest` run by Arthur's provider (rulings 78, 94, 96).
Lane: `registers/parliament`; the pull is `support/mcpsource`. Draft, held in
the lane's folder because the fence keeps a build session out of
`docs/legal/positions/`; the integrator moves it there. Written 27 October
2026 by parliament-1.

**Finding: the material is Parliament's public record and copying it is
lawful (most of it has no copyright at all); the doubt is in how it was
captured. The provider got past a challenge with a proxy pool, which the
estate itself may never do (hard limit 6). The estate fetched nothing and
holds the records on the provider's capture: that is the question for the
lawyer.**

**How the material reached us.** The estate fetched nothing from
parliament.nz or the Parliament API, and its fetch gate holds that host
(ruling 78: no permission request sought; the Hansard challenge held at 23
September closed the same way). Arthur's provider captured the API and the
site on its own box, outside the estate, and serves the records through the
MCP over an SSH tunnel (`qv4-mcp-tunnel`). The archived pages it took from
web.archive.org (each record names the archive's copy, `snapshot_url`), not
from parliament.nz. The estate's pull asks the MCP for records, one request
at a time, 200 a page, and lands each whole by hash. No model made any field
of these corpora: written questions and bills are pure API mirrors (no
capture block); the rest carry the provider's capture block, kept whole.

1. **Is the page open?** Parliament's pages and the API's documents are
   published for the public with no login. But parliament.nz serves a
   challenge to automated readers: the estate's own Hansard reader met it in
   September and stopped. The provider passed it with a proxy pool. The estate
   did not get past any lock, challenge or block (hard limit 6), and could not
   have captured this itself. For the lawyer: whether records a third party
   captured by passing a challenge the estate may not pass can be held and
   shown, given the material itself is public; and whether that changes if
   Parliament objects. A publisher's direct request to stop is honoured (hard
   limit 7): if Parliament asks, the lane stops taking the corpora.
2. **Is storing it lawful copying?** The Copyright Act 1994, s 27(1), puts no
   copyright in Bills, Acts, the debates of the House, or the reports of
   select committees laid before the House. Written questions and their
   replies are published by the House as part of its proceedings; the bills,
   SOPs and committee reports are within s 27. The site's other content
   (pages, calls for submissions, features) is the Office of the Clerk's and
   the Parliamentary Service's; Parliament states its own reuse terms on its
   copyright page, which the lawyer or Arthur reads (the estate may not fetch
   it); New Zealand government bodies mostly publish under NZGOAL, Creative
   Commons Attribution 4.0. The Internet Archive's copies are of the same
   pages. Every row cites its document's hash and, where the record gives
   one, the page's own address.
3. **What terms did we accept?** None with Parliament or the Internet Archive
   (the estate never visited either). With the provider, whatever Arthur agreed
   when he set up the MCP (ruling 94); its server says only "Consumers may
   ingest the full corpus through the `records` tool". Those terms, in
   writing, belong on this page before anything is sold.
4. **What does privacy law, or the statute, limit?** Written questions name
   members and ministers in their public roles; a question or reply sometimes
   names a member of the public, an official, a company or a place. Parliamentary
   privilege covers the House's own publication, not ours: our holding is under
   the Privacy Act 2020. The published views carry no question, reply or page
   text (they stay in the lane's tables and the private twin; the board opens a
   document whole, ruling 88). No address column exists (hard limit 15).
   Archived pages from 2006 on may print MPs' office details or a person in a
   story; their text is in `parliament_private.wayback_texts` only. A name a
   court has suppressed is suppressed here too (hard limit 16).

Crawl delay: not applicable (nothing fetched from the host). Floor for the
MCP: one request at a time, a second between pages, a call waited for up to
three minutes and retried after 30 s doubling to 10 minutes; the nightly pull
runs off-peak NZ time. Author: parliament-1 (Opus), 27 October 2026. A lawyer
reviews this page before anything is sold.
