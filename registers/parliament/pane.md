# Parliament's records, on the board

Three panes, one per published view. Every row notes that the estate did
not fetch parliament.nz: the provider captured it off-estate, through a
challenge the estate may not pass (ruling 78, hard limit 6).

**A written question** (`pub.parliament_written_questions`): its number and
year (`question_number`, `question_year`; numbered afresh each year) and the
Parliament, the title as the API gives it ("<number> (<year>). <member> to
the <minister>"), the minister and their title, the day it was released,
and whether a reply is held. The question and the reply are held whole in
the lane's own table (`parliament.written_questions`) and open with the
document (ruling 88); no view carries them. The citation is the
document's hash with Parliament's own document id (`document_id`,
`WQ_<number>_<year>`): the API gives no page address, and none is made up.

`member_id` is Parliament's own id for the asking member, the same id
`registers/hansard`'s speech turns carry (`pub.hansard_speeches.member_id`).
So a join to Hansard is declared by that id, never by a name. The House's
`pub.members` has no such id: a join from a written question to a member
of the House goes through Hansard's id, or is not made. Measured 27 October
2026 on the full build: 300 member ids ask the 674,846 questions that carry
one (8,678 carry none); 94 of them are among the 128 ids in Hansard's turns
(20 November 2024 to 23 September 2026) and ask 389,530 of the questions.
The questions run from 2003 to 2026.

**A bill, committee paper or SOP** (`pub.parliament_api_items`): the corpus
(current bills, historical bills, calls for submissions, select committee
reports, supplementary order papers) and the API's `documentType`; the
title, the bill number and current stage, the committee, the member and
party where the API gives them, the dates as served. A current bill is in
both bill corpora: two rows, one per corpus. A call for submissions links
to its page on parliament.nz (`citation_url`); the others have no address
in the record and cite the document's hash. The provider's capture block is
shown whole.

**An archived page** (`pub.parliament_wayback_pages`): the page's own
address, the Internet Archive's copy the provider read (`snapshot_url`) and
its stamp, the page's title, type and word count. The text opens only with
the document (ruling 88); no view carries it.

A record the MCP no longer serves (`served` false) is shown struck through
with "withdrawn by the source"; a record served in more than one version
says "read from the version taken last, of N".
