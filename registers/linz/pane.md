# LINZ, on the board

One pane, counts only (no owner's name):

- **Pulls:** `select source, pull_id, stated, finished_at from linz.pulls order by started_at desc limit 6`; pages landed per pull
  from `linz.pages`.
- **Against the source:** `python -m registers.linz.check`: each source's rows read against the service's stated count.
- **Read:** `select source, stated, landed, read, aside from linz.loaded_pulls`; owners by kind,
  `select kind, count(*) from linz.owners group by kind`.
- **Set aside:** `select source, stage, reason, count(*) from linz.read_set_aside group by 1, 2, 3`.
- **Last run:** the newest `qv4-linz-capture` and `qv4-linz-load` run records.
