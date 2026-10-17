After a standby is promoted its live-row statistics (`pg_stat_user_tables.n_live_tup`) read zero for every table, so measure rows from `pg_class.reltuples` (replicated from the old primary's last analyse) or count them.
area: measuring, databases, failover, baseline
paid-for-by: 2026-10-18, founding session 2, step 1.3

The first pass at the baseline listed the largest tables of the three old
databases with `n_live_tup` beside them, and every big table read 0 while
its size read gigabytes. The statistics collector's counters are per
cluster and are not replicated, so a promoted standby starts them from
nothing. `pg_class.reltuples` is a catalogue column and comes across with
the data, so it still holds the last analyse's estimate from the old
primary.

How to apply: on node2 while it is the primary, and on any freshly
promoted or rebuilt box, do not read a zero in the live-row statistics as
an empty table. Use `reltuples` for an estimate and a count for the truth,
and say which one a figure is.
