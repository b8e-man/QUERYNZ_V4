A body with several rows on one register (a charity deregistered and registered again under a new number, one NZBN) is removed only where its last registration is: "any row removed" read a live re-registered charity as gone.
area: links, rules, bodies, body_dates, charities, NZBN, organisation-sole-company, organisation-one-live-company, check item 9
paid-for-by: 2026-10-30, fix-links-6, the card "the bodies check is red on a placeholder NZBN and one NZBN under two charity numbers"

Why: the fix for "no NZBN names two bodies" folded CC58580 (deregistered
February 2023) and CC61425 (registered July 2023, the same NZBN) into one
body. `rules.body_dates` and the check's SQL both took a body as removed
where any of its deciding rows said so, which was right while a body had
at most one row per register; with two charities rows the merged body read
as removed on 2023-02-20 and a 2024 row naming the charity would have
stayed near, "removed before the row's date", though the charity stands.
The single-row case already had the rule in words ("a charity re-registered
after a deregistration is registered: the old date is not its removal");
the multi-row case needed it in code, in Python and in SQL alike, which is
why the two are now one text (`rules.body_dates_sql`).

How to apply: when a fold makes a body hold several rows of one register,
decide its removal from the row registered last (none counting earliest,
then the largest ref by bytes), and keep the Python rule and the check's
SQL from one place so they cannot drift. The formation registers (a society
or limited partnership and its Companies Office twin) keep "any row
removed": that is ruling 114's reading and was not changed here.
