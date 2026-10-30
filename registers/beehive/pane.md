# Beehive releases, on the board

One pane per release, speech or feature (`pub.beehive_releases`): the
title, the type as the site gives it, the day (`published_on`, the
record's own date; `published_at` as served, never re-zoned), the word
count, and the page's address as the citation, with the document's hash
small beneath it. Then the ministers the site tags it with, in order
(`pub.beehive_release_ministers`, each with the site's slug), and the
portfolios. Then, set apart under the heading "The source's annotation
(made by its model, not ours)", the topics and quotes
(`pub.beehive_release_annotations`): shown as the provider's, never as a
finding of the estate, and never offered as a link. A release served in
more than one version says "read from the newest of N versions". Where the
row's fields are the old estate's (`origin` "old estate": its scraper's
title, day and text, original not held), the pane says so; where the MCP
holds the page only as a capture its provider has not yet read
(`mcp_state` "captured only"), the pane says "captured by the provider
on <captured_at>, not yet read" beside the old estate's reading, and the
MCP's reading replaces it once the provider reads the page. The body
is not in any view; the board's document opener shows the record whole
(ruling 88). Every row notes that the estate did not fetch the page: the
provider captured it off-estate (ruling 78).

The text reader's work (Arthur, 31 October 2026), counts only, never a
name: `select reading, count(*) from beehive.releases group by 1` (read,
waiting: text reader, set aside, not read: old estate export) and
`select count(*), count(distinct document) from beehive.people`, with
`select kind, count(*) from beehive.people group by 1` and the same by
`role`: names read, documents read, documents waiting, documents set aside
at read (the reason in `beehive.set_aside`, stage `read`). A release's
pane shows its one-line summary and the model that made it (`summary`,
`read_model`), then the names the reader found (`pub.beehive_people`:
name as printed, kind, role, the role as the text says it, the
organisation a person is of), set apart under "Names the text reader
found (ours, model-made, never a link)". The site's tagged ministers stay
in their own list above and are not re-read. `python -m
registers.beehive.check` holds the account.
