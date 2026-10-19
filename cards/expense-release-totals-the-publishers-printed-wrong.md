# Expense release totals the publishers printed wrong
kind: finding
state: open
use-case: 1
session: interests-expenses
opened: 2026-10-20

The lane checks each release's printed grand total against the sum of its
lines (`python -m registers.expenses.check`). On the full set, 20 October
2026: all 31 members' grand totals equal their rows; two members'
releases print a category total that does not (October to December 2022:
the Inter-Parliamentary Office's grand total, $131,106, leaves out
Labour's $165,368; October to December 2025: $516.19 moved between the
two accommodation columns in the National and grand totals). Of 72
Executive release tables, 64 grand totals equal their rows and 8 do not;
and 23 ministers' lines do not add to their own sub total (Steven Joyce,
October to December 2012: categories $55,179, sub total printed $27,215),
which the lane sets aside, never publishes.

Every case looked at is the publisher's arithmetic: the cells match
LibreOffice's reading of the same files exactly. The check therefore
fails on these releases every time it runs. At the checkpoint: accept onto
the known-limits page (the release's figure and ours are both shown), or
keep a list of known differences the check passes over.
Blocks: nothing.
