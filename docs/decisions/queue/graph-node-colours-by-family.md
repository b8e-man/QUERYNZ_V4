# Graph nodes: one colour per family of registers, or one per register
default: One colour per family (14 families of the 28 registers), each 3:1 or more on the picture and 17.5 or more apart
blocks: Nothing
recommendation: The default. The board holds 28 registers, and no 28 colours are each 3:1 on the dark picture and 15 apart in OKLab (OKLab is a colour space where distance tracks how different two colours look; 15 is the floor the key's edge colours meet). The best 28 found are 13.5 apart, so some pairs would be hard to tell apart. Fourteen families keep every colour easy to tell from every other; a node's own register is in its hover and the legend's.
raised: 2026-10-26 by board-7 (ruling 100)

Ruling 100 says "round nodes coloured by register". The brief asked for
each colour at 3:1 on the picture and 15 apart, like the edge colours. Both
cannot hold for 28 registers. Families, as built (`catalogue.FAMILIES`):
party donations; candidate returns; parties; party finance; the House;
declared interests; expenses; companies; societies and charities; iwi;
public money (grants, tenders, contract disclosures); regulators (Commerce
Commission, FMA, WorkSafe, building practitioners, overseas investment);
courts and sanctions; notices and minutes.

The other choice is 28 colours with the floor lowered to 13 for nodes.
Either is a change of data in `catalogue.FAMILIES` and one number in
`panes.contrast_problems`, not a rewrite.
