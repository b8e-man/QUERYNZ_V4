# Entities, on the board

The links lane publishes no register of its own; what it adds to the board
is the entity: the rows of every register that are one person or one body.
`pub.entities` (ruling 123) is one row per entity, and every reader (the
board, the scan, the report, the site) draws an entity from it. Nothing
here is a new link: the view is read from `pub.groups` and `pub.names`
alone.

## What an entity is

- **A group** of `pub.groups`: rows joined by confirmed links and `same`
  decisions, minus the pairs a decision takes out. `entity_id` is the group
  id, the group's smallest row key by bytes.
- **A lone row**: a row of `pub.names` in no group is a single-row entity.
  `entity_id` is the row's ref (`<register>:<key>`). A coupled donor's part
  row (ruling 73, ref `<donor ref>#<n>`) is a row of `pub.names` and so an
  entity like any other until a link gathers it.
- A group that holds no row of `pub.names` (two bodies joined by their
  official number, `official-number@1`: a company and its Gazette
  liquidation row) is an organisation, named from the bodies table.

## The columns

| Column | What it is |
| --- | --- |
| `entity_id` | The group id, or the lone row's ref. A reader opens the entity by it: its rows are `pub.groups` where `group_id = entity_id`, or the one row of `pub.names` where `ref = entity_id` |
| `kind` | `person`, `organisation` or `estate`, as `pub.names` has it: the kind of the row that gives the display name |
| `display_name` | The name the entity is shown under, chosen by the ordering below |
| `rows` | How many rows the entity holds (1 for a lone row) |
| `registers` | The distinct registers of its rows, sorted by bytes |
| `contested` | The group is contested (the watch flagged a link in it, or a `not the same` decision contradicts it); never for a lone row |
| `politician` | Any row of the entity is a politician's (as `pub.names` marks it) |
| `built_at` | When the build made it, the groups' own build |

## The display name: one ordering every reader shares

Among the entity's rows of `pub.names`, the filed name (`name_filed`, its
whitespace folded to one space and trimmed) is chosen by:

1. **the most words**, then
2. **the most characters**, then
3. **the earliest row by ref**, compared as bytes (`COLLATE "C"`, the
   lane's one order of refs, `links.ORDER`).

So "John Andrew Smith" is chosen over "John Smith", "John Smith" over "J
Smith", and of two rows filed "John Smith" the one whose ref is smallest
by bytes. This is ruling 105's decision 1 as the board's `people.fullest`
already reads it, so a reader that still has its own copy of that rule
chooses the same name; it should read this column instead and never
re-derive it. Where the group holds no row of `pub.names`, the same
ordering runs over the names of its bodies in `links.bodies`.

A suppressed name is never in `pub.names`, so it is never a display name
and never counted in `rows` (hard limit 16). No address is in the view.

## On the board

An entity appears as the results pane's entry and the dossier's heading:
`display_name`, then `rows` and the count of `registers`, with the
`contested` and `politician` marks. The graph's one state (ruling 120) is
these entities, each a node. The lane's own line on the board: the
outside check's item 11 (the entities equal the groups plus the lone
rows) and the last `qv4-links-build` run.
