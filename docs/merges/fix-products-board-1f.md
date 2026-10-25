# fix-products-board-1f: use-case names open their interfaces in a new tab (ruling 89); a db connection counter (ruling 90)
branch: fix/products-board-1 (pushed, 317b94a; one commit on 56cdcff; merge after fix-products-board-1e)
session: fix-products-board-1 (Opus, fix, scope products/board/; sixth use of the name)
raised: 2026-10-26 (written to the session's scratch folder: the fence refused the inbox link; move it to
inbox/merge-requests/)
claims: products/board/ (uses.py, panes.py, server.py, db.py, check.py, spec.md, units/qv4-board.service;
tests/test_uses.py); docs/status/board.md. No card opened or closed. Lesson: nothing new.

## What it does

1. **Report templates counted built (ruling 89).** `uses.read_templates` reads `products/templates/*/template.toml`
   as files (tomllib, never imported) beside the scan's. Use case: the `use_case` field, else the owner line's
   "(use case N)", else the folder's leading two digits (the ten report templates' owner lines name a session, so
   the digits decide). Each template carries its shape: "Subject report" or "Register scan". The tab shows 13 use
   cases with templates built: 10 report (2 to 8, 11 to 13), 3 scan (9, 10, 14).
2. **Each name is a link, `target="_blank" rel="noopener"` (ruling 89).** Report: `<report>/?template=<name>`, the
   report server's `GET /` form with the template chosen. Scan: `<scan>/scan/<name>`, the first template on the
   name, the rest beside ("also: …"). Follow the Money (shape "Published site"): `<site>/`. 15 says "held: ruling 79
   (no document reading until node1 returns)"; 16 and 17 "held: ruling 63 (step 7)"; no link (`uses.HELD`).
   Ports and the host rule in one place, `uses.SERVERS` / `uses.bases`: `QV4_REPORT_URL`, `QV4_SCAN_URL`,
   `QV4_SITE_URL` when set, else `http://<request Host header, port off>:<8440|8450|8430>`; never 127.0.0.1.
   The unit gains `QV4_SCAN_URL=http://10.0.0.2:8450 QV4_SITE_URL=http://10.0.0.2:8430` beside `QV4_REPORT_URL`.
3. **Connection counter (ruling 90).** Every page's bar ends `db <in use>/<max_connections>`, hover title the count
   by login (qv4_product, qv4_owner, qv4_read, qv4_oldread, other). One query per page (`db.CONNECTIONS`:
   pg_stat_activity, `backend_type = 'client backend'`, grouped by usename, with `current_setting('max_connections')`)
   on the product reader: the graph and use-case pages reuse their own; the search tab and the lists open one short
   product-reader connection for it. On any failure the bar says `db ?` and the page renders. Live just now:
   `db 4/100`, all qv4_product.
4. **Check.** Case 14 widened: every folder holding a template.toml under `products/templates/` and
   `products/scan/templates/` binds to exactly one row of the plan's table, else "an orphan". The scan shape's own
   two step 6.1 templates (donors-named-as-companies, society-officers-liquidations) serve no use case and are named
   in `check.SHAPE_OWN`; a new use-case-less template fails. Every use case but 15 to 17 has a link, those three
   say their hold, every link on the table has target and rel. Case 15: the counter is on the page, total >= 1.
   Shown red in-process with SHAPE_OWN emptied and two holds removed (four problems), green restored.
5. **Tests** (`test_uses.py`, 5 → 12): the fixture's 13 built (10 report, 3 scan) and 15 to 17 held without links;
   15 links, each with target and rel; report link equals a copied `REPORT_FORM = "/?template="` and the report
   server's source (read as text) still routes `GET /` with `get("template", …)`; host rule incl. IPv6 and the env
   override; folder-digit fallback; the counter from a fixture answer and `db ?`. Slow: every link on the real tab
   answers 200 on localhost, skipping with the reason printed when a server is down (ran: all 200).

## Runs

- `QV4_INTEGRATOR=1 bin/fast products/board`: green in 42.2 s.
- `python -m products.board check` against live data: green (27 s).

## The integrator must

1. Move this file into `inbox/merge-requests/`.
2. Merge after `fix-products-board-1e`.
3. Install `products/board/units/qv4-board.service` (two new settings) and restart `qv4-board` at the release.
   Expected: the use cases tab shows 14 linked names and 3 held; the bar reads `db n/100`.

## Result (integrator, 26 October 09:45 NZDT)

Merged as d50592f: fast tier green (628 s), gate green, nothing to load.
Moved from the session's scratch folder into the inbox by the integrator.
Working copy and branches retired; release copy moved; the board unit
reinstalled with QV4_SCAN_URL and QV4_SITE_URL and `qv4-board` restarted;
the use-case links and the connection counter answer on the live board.
