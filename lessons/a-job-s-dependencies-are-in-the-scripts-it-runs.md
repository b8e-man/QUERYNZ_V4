A job's dependencies are in the scripts it runs, not its unit file: trace every address each script opens, defaults included; the release reached the product through an argparse default no unit, port list or gateway route showed.
area: 1.4, old estate, carve-out, job control, founding
paid-for-by: 2026-10-18, founding session, the batch 2 check that missed querynz-pi-web

Before batch 2 the check read the carve-out's unit files and the gateway's
routes and found no call to :8300, so `querynz-pi-web` went on the stop
list. `ops/pi_release.py` runs sixteen gate scripts; one of them,
`pi_search_gate.py`, has `--base` defaulting to `http://127.0.0.1:8300`
and is run without `--base`. The trace that finds it is: list what the
job's program runs (subprocess calls), then grep each of those for
addresses and argparse defaults. Done after the fact it took ten minutes
and cleared the other seventeen units in the batch.
