# LINZ, on the board

One pane, counts only (no owner's name):

- **Pulls:** `select source, pull_id, stated, finished_at from linz.pulls order by started_at desc limit 6`; pages landed per pull
  from `linz.pages`.
- **Against the source:** `python -m registers.linz.check`: each source's rows read against the service's stated count.
- **Read:** `select source, stated, landed, read, aside from linz.loaded_pulls`; owners by kind,
  `select kind, count(*) from linz.owners group by kind`.
- **Street addresses (private, counts only):** `select count(*), count(distinct title_no) from linz_private.title_addresses` against `select count(*) from linz.titles`; never a value on the board's pane.
- **Set aside:** `select source, stage, reason, count(*) from linz.read_set_aside group by 1, 2, 3`.
- **Last run:** the newest `qv4-linz-capture` and `qv4-linz-load` run records.
- **Everything else (ruling 142):** `select source, stated, landed from linz.loaded_pulls where source not in ('titles', 'owners', 'place_names', 'property_titles', 'property_addresses', 'addresses') order by landed desc`; what the catalogue takes and why it leaves the rest, `registers/linz/catalogue.py`; the night's due order, `capture.DUE_ORDER`.
- **Addresses by geometry (private, counts only):** `select count(*), count(distinct title_no) from linz_private.title_address_points`, the titles the spine gives none reached through their parcels' polygons; the load's line says how a sample of spine titles agrees.
