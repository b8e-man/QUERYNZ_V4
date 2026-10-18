# Tenancy Tribunal orders, on the board

One pane, counts only (no names, no addresses, nothing from inside an order):

- **Held:** `select count(*) filter (where document is not null), count(*) from tenancy_tribunal.orders`:
  orders landed, of orders listed.
- **At risk:** `select count(*) from tenancy_tribunal.orders where document is null and unpublished_date < current_date + 14`:
  listed, not yet held, and leaving the source within two weeks. Above zero is the number that matters.
- **Against the source:** `python -m registers.tenancy_tribunal.check`: months equal, short, past the window.
- **Set aside:** `select stage, count(*) from tenancy_tribunal.set_aside group by stage`.
- **Last run:** the newest `qv4-tenancy-tribunal-capture` run record: requests, landed, why it stopped.
