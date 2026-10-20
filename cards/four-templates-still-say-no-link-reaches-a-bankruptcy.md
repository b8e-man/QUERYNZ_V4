# Four templates still say no link reaches a Gazette bankruptcy, and block a check that can run
kind: finding
state: open
use-case: 2 legal; 3 banking; 4 agriculture; 13 ownership
session: construction-1
opened: 2026-10-21

Since links-2 (20 October), `pub.names` carries 64,747 bankruptcy rows and
the person rules join them: measured 2026-10-21, 8,031 confirmed
(`full-name@1`) and 18,424 near (`name-only@1`) links touch a bankruptcy
row. The legal, banking, agriculture and ownership templates still end
their bankruptcy rule with "no link rule joins one to a person yet" and
block it on every report, and their limits pages say a bankruptcy cannot
be seen. A confirmed row still fires (their rules read the section first),
so nothing shows wrong; but the check never clears where it could, and the
pages mislead. A fix in each folder: the prohibition rule's guard (links
built, every link read) for the clear, as the construction template's
`bankruptcy` does, and the limits line updated.
