# The scanned party statements' figures are not read
kind: finding
state: open
use-case: 1
session: party-finance
opened: 2026-10-20

The statement reader takes text-layer pages only. Of 92 pairs (46
statements, operating and position), 46 publish and 46 are catch-log
lines (`party_finance.set_aside`, stage `statement-figures`):

- 20: ten statements with no text layer at all (ACT 2025, Freedoms NZ
  2024, Leighton Baker 2024, New Nation 2024, NZ First 2024 and 2025, NZ
  Outdoors & Freedom 2024, Opportunity 2026, Vision NZ 2024 and 2025).
- 12: text layers that are boilerplate around scanned accounts (National
  2024 to 2026, NZ First 2024 audited, ACT 2026, Women's Rights 2024):
  no headline line in the text.
- 12: a position with no `Total Liabilities` or no `Total Assets` line
  (the statement lists "Assets Nil", or a balance of liabilities and
  surplus, or no balance sheet), and two one-line or empty income
  statements (Democratic Alliance 2024, NZ Outdoors & Freedom 2025).
- 2: the statement's own arithmetic does not hold (Aotearoa Legalise
  Cannabis 2024, NZ Loyal 2024); these are findings about the statements.

Next: the same pairs from the page reader's stored readings (33 of 46
statements have them under v1; the rest need a page-reader job), measured
the same way. The reader's line parser expects layout columns; a stored
reading's tables come as markdown or plain lines, so it needs its own
tokeniser and the same two checks.

reconcile-1 (21 October, ruling 66): the arithmetic set-aside is now one, NZ Loyal 2024 ($80,354.02 out); Aotearoa Legalise Cannabis 2024 is reconciled with issue `-0.21`.
