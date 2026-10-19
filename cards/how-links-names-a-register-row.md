# How links names a register row, for the board to read back
kind: finding
state: open
use-case: -
session: board
opened: 2026-10-20
closed:

`links/tables.sql` says a link's `row_a`/`row_b` is "a register row's stable
key, schema-qualified: 'companies:1234-D5'". The published keys are not of
that shape (`companies/9429000001311/director/e5a990cc784e`,
`ge-2020/delamere-tuariki/auckland-central`, `<sha256>/A/1`), and several
views share a key shape, so a key alone does not say which view holds the
row. The board assumes `<register>:<key>` (the lane's folder name, a colon,
the published key) and finds the view by trying each view of that register
(`links_view.py`). When step 4.2 builds the links, the links session settles
the form and publishes `pub.links`, `pub.groups`, `pub.decisions`; if the
form differs from the board's assumption, `links_view.ref` and `split_ref`
are the two functions to change (a fix session, `products/board`). Until
then every pane says "no links built yet", and the person pane's group is
the row alone, with namesakes apart.
