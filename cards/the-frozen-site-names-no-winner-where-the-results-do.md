# The frozen site names no winner where the results do
kind: finding
state: open
use-case: 1
session: comparison
opened: 2026-10-20

Nelson 2020 and 2023: the frozen electorate page shows no winner (its join
of the result to the candidate-return summary failed on the name); the
rebuilt page names Rachel Boyack from the house lane's seats, and she won
both. The comparison folds name forms ("Rachel Elizabeth BOYACK") before
it compares, so only a missing winner is a difference.

Which side is right: the rebuilt one. Not fixed in the frozen product
(hard limit 19). Owner: comparison.
