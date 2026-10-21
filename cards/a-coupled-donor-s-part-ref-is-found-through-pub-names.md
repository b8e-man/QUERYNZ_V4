# A coupled donor's part ref is found through pub.names
kind: finding
state: open
use-case: 1
session: coupled-1
opened: 2026-10-21

Ruling 73 is built in links (coupled-1): a donation row filed as two people
("Greenlees, Craig & Shayne") gains one part row per person, ref
`<donor ref>#<n>` (`party_returns:<key>#1`), joined to the donor row by
`coupled-name@1` and to other people's rows by the usual rules. `pub.names`
carries each part with the donor row's `view` and `key` and `part_of` = the
donor's ref.

The readers outside links take the key from the ref (`split_ref`):
`products/report/rows.locate`, `products/board/links_view`, the walk. A part
ref's key ends in `#<n>`, so they find no row and a person's walk that
reaches a part shows nothing where the coupled donation should be. Fix: read
a ref through `pub.names` (`view`, `key`) or `part_of` before `split_ref`.
Owner: report and board (and the site, if a person page is to show the
coupled donation; the donor page is unchanged, the donor row keeps its key).
