A filed name in the couple shape ("X and Y Z") is not two people until one of its given names is one the director register knows: "Bread and Roses Auction" passed the old recogniser as a couple.
area: keys.names (is_joint_name, joint_parts), links.rows (coupled donor parts), any rule that cuts a filed name into people
paid-for-by: 2026-10-21, coupled-1, ruling 73

`is_joint_name` matched "A & B Surname" by capitals alone, so a candidate
return's "Bread and Roses Auction" read as two people, harmless while the
answer was only a flag and wrong the moment the links cut it into "Bread
Auction" and "Roses Auction". The same day the published donor tables showed
real couples it missed ("Stephen B & Virginia Fisher", "Douglas, Jeffrey
Graeme & Christine Elizabeth", "Stewart Menzies and Megan Jean Harrison").
Before a recogniser starts producing rows, run it over every distinct filed
string of its views (they are a few dozen) and read both lists: what it takes
and what it leaves.
