# Two rows of one name whose star centre is a third row
default: Not joined. The scan reads a name-only@1 link between the two rows' groups (links/spec.md, contract for readers) and a full-name@1 link between the two rows, and the lane stores neither link between two leaves of a star
blocks: 30 lines of the stored runs stay red in the scan's read-back (procurement-directors-donors run 154: 29 of 80; procurement-shareholders-donors run 155: 1 of 6) until qv4-scan-rerun runs them again. After that, which pairs show still depends on which row the lane makes the centre
recommendation: The links lane draws name-only@1 as the contract's words say, one link per pair of components (not a star from one), and says in the contract how a reader finds a full-name@1 pair (the group, or a link per pair)
raised: 2026-10-29 by fix-products-scan-1

The links lane stores `name-only@1` as a star. For each first-and-last name
it draws one link from the group with the smallest key to every other group
of that name (`links/build.py` `near_links`). It stores `full-name@1` the same
way, one star per full name. The contract on integrate/fix-links-5 says "one
link per pair of components" and "nothing a reader shows may depend on" which
row is the centre. A star can't meet both. Two leaves share no link and no
stored reason. The near reason (middle names differ, one middle, none) is
worked out for each pair, so a reader can't borrow the centre's reason.

Measured live on 28 and 29 October, read-only, against the stored lines:

- Director lines (80): 46 still have a near link between the two rows, 4 a
  confirmed one, 1 is found only between the two groups (green again), 28 are
  two leaves of one name-only star, and 1 is a confirmed pair in one group
  whose full-name star moved off both rows.
- Shareholder lines (6): 5 have a near link between the rows, and 1 is a
  confirmed pair in one group, as above.
- The eleven lines the brief named (director lines 1 to 11) are all among
  the 28 leaves.

The new walk on today's links gives 142 director and 139 shareholder lines.
Every line the old walk gives today is among them, and every one reads back
green.
