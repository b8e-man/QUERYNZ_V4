A view of entities is the groups plus the rows in no group, and a group may hold no row of the names table at all (two bodies joined by their official number), so name it from the bodies table and count it against the groups, never from the names alone.
area: links, entities, groups, pub.entities, bodies, check

Why: links-4 built `pub.entities` as one row per group plus one per lone row of `links.rows`. On live 4,333 of the 724,964 groups hold only a company and its Gazette liquidation row, joined by `official-number@1`; neither is in `links.rows`, so a name taken from the rows alone is blank for every one of them, and a count taken from the rows alone is 4,333 short of the groups. The brief's figure (2,597,213 = 724,964 groups + 1,872,249 lone rows) only agrees when the entity is counted from `links.groups` first and the rows second.

How to apply: start an entities build from `groups` (every group id) and add the rows in no group; take the display name from the rows where the group has any and from `links.bodies` where it has none; make the outside check count groups without an entity and lone rows without an entity separately, so an offsetting error cannot hide in a sum.
