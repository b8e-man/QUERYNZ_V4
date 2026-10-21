A "to the cent" check written in floats (`abs(a - b) <= 0.011`) passes a one-cent difference silently; compare in integer cents, and give any admitted difference a column of its own.
area: registers, reconciliation, political-donation documents (ruling 66)
paid-for-by: 2026-10-21, reconcile-1

The candidate-returns declaration reader chose its pairing of figures and
labels with `<= 0.011`, a margin meant to absorb float error. It admitted
five returns whose expenses parts were a cent off the printed total, and
nothing on the row said so. Ruling 66 makes a difference below $100
reconcilable but never silent: the lane's `reconcile.py` turns both sides
into integer cents (Decimal, half up), a difference of 0 is equal, and
anything else that is admitted writes `issue` on the row. Replaying with
the strict comparison is what found the five; the replay's `compare`
only shows it if the new column is in its output.
