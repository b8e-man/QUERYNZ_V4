"""The takeover jobs run against stand-in commands: the box's state (address held, database up, standby or
primary, something answering on the wire) lives in files, and every command the scripts call is recorded.
Each refusal is tested by what must NOT happen (no promote, no address, no rewind)."""
import os
import pathlib
import subprocess

import pytest

SYSTEM = pathlib.Path(__file__).resolve().parents[1] / "system"

STUB = r"""#!/bin/bash
S="$QV4_STATE"
echo "$(basename "$0") $*" >> "$S/calls"
case "$(basename "$0")" in
  hostname) echo "${QV4_STUB_HOST:-node1}" ;;
  ip)
    if [ "$1" = addr ] && [ "$2" = add ]; then touch "$S/vip"; exit 0; fi
    if [ "$1" = addr ] && [ "$2" = del ]; then rm -f "$S/vip"; exit 0; fi
    [ -e "$S/vip" ] && echo "2: enp13s0    inet 10.0.0.10/24 scope global enp13s0"
    echo "2: enp13s0    inet 10.0.0.1/24 scope global enp13s0" ;;
  arping)
    if [ "$1" = -D ]; then [ -e "$S/wire_answers" ] && exit 1; exit 0; fi ;;
  systemctl)
    case "$1" in
      is-active) [ -e "$S/pg_up" ]; exit $? ;;
      stop) [ -e "$S/stop_hangs" ] || rm -f "$S/pg_up" ;;
      kill) [ -e "$S/stop_hangs" ] || rm -f "$S/pg_up" ;;
      start)
        if [ "$2" = postgresql ]; then touch "$S/pg_up"; [ -e "$S/streams_after_start" ] && echo streaming > "$S/receiver"; fi ;;
    esac ;;
  runuser)
    shift 3   # -u postgres --
    if [ "$1" = pg_rewind ]; then [ -e "$S/rewind_fails" ] && exit 1; exit 0; fi
    q="${@: -1}"
    case "$q" in
      *pg_promote*) rm -f "$S/recovery"; echo t ;;
      *pg_is_in_recovery*) [ -e "$S/recovery" ] && echo t || echo f ;;
      *status*pg_stat_wal_receiver*) cat "$S/receiver" 2>/dev/null || true ;;
      *flushed_lsn*) echo 1/10 ;;
      *">="*) echo t ;;
      *timeline_id*) echo 7 ;;
      *) echo 1/10 ;;
    esac ;;
esac
exit 0
"""


@pytest.fixture
def box(tmp_path):
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    for cmd in ("hostname", "ip", "arping", "systemctl", "runuser", "sleep", "chown"):
        p = bin_ / cmd
        p.write_text(STUB)
        p.chmod(0o755)
    state = tmp_path / "state"
    state.mkdir()
    pgdata = tmp_path / "pgdata"
    pgdata.mkdir()
    (pgdata / "PG_VERSION").write_text("18\n")
    (pgdata / "postgresql.auto.conf").write_text(
        "max_connections = 400\nprimary_conninfo = 'host=10.0.0.2 user=x password=old'\nprimary_slot_name = 'stale'\n")
    creds = tmp_path / "replication.env"
    creds.write_text("REPLICATION_USER=replicator\nREPLICATION_PASSWORD=pw-for-the-test\n")
    sysnet = tmp_path / "net" / "enp13s0"
    sysnet.mkdir(parents=True)
    (sysnet / "carrier").write_text("1\n")
    env = dict(os.environ, PATH=f"{bin_}:/usr/bin:/bin", QV4_STATE=str(state), QV4_PGDATA=str(pgdata),
               QV4_MARKER=str(tmp_path / "etc" / "not-primary"), QV4_REPLICATION_ENV=str(creds),
               QV4_TAKEOVER_LOG=str(tmp_path / "log"), QV4_SYSNET=str(tmp_path / "net"), QV4_LINK_WAIT="1")

    class Box:
        def __init__(self):
            self.state, self.pgdata, self.marker, self.env = state, pgdata, pathlib.Path(env["QV4_MARKER"]), env

        def set(self, *names):
            for n in names:
                (state / n).touch()

        def run(self, script):
            r = subprocess.run(["bash", str(SYSTEM / script)], env=self.env, capture_output=True, text=True)
            self.out = r.stdout + r.stderr
            return r.returncode

        def calls(self):
            p = state / "calls"
            return p.read_text() if p.exists() else ""

        def has(self, name):
            return (state / name).exists()
    return Box()


def test_takeover_refuses_while_something_answers_for_the_address(box):
    box.set("pg_up", "recovery", "wire_answers")
    box.marker.parent.mkdir(); box.marker.touch()
    assert box.run("takeover.sh") == 1
    assert "pg_promote" not in box.calls()
    assert not box.has("vip") and box.marker.exists()


def test_takeover_refuses_a_box_that_is_not_a_standby(box):
    box.set("pg_up")
    assert box.run("takeover.sh") == 1
    assert "pg_promote" not in box.calls() and not box.has("vip")


def test_takeover_promotes_reserves_the_peers_slot_and_takes_the_address(box):
    box.set("pg_up", "recovery", "receiver")
    box.marker.parent.mkdir(); box.marker.touch()
    assert box.run("takeover.sh") == 0, box.out
    calls = box.calls()
    assert "pg_promote(true, 60)" in calls
    assert "pg_create_physical_replication_slot('node2_standby', true)" in calls
    assert calls.index("pg_promote") < calls.index("ip addr add 10.0.0.10/24")
    assert box.has("vip") and not box.marker.exists()


def test_release_marks_drops_the_address_and_stops_a_primary_cleanly(box):
    box.set("pg_up", "vip")
    assert box.run("release.sh") == 0, box.out
    assert box.marker.exists() and not box.has("vip") and not box.has("pg_up")
    assert box.calls().index("checkpoint") < box.calls().index("systemctl stop postgresql")


def test_release_leaves_a_standby_running(box):
    box.set("pg_up", "recovery")
    assert box.run("release.sh") == 0, box.out
    assert box.has("pg_up") and "stop postgresql" not in box.calls()


def test_rejoin_refuses_on_the_box_holding_the_address(box):
    box.set("vip", "wire_answers")
    assert box.run("rejoin.sh") == 1
    assert "pg_rewind" not in box.calls()


def test_rejoin_refuses_when_no_primary_answers(box):
    assert box.run("rejoin.sh") == 1
    assert "pg_rewind" not in box.calls()


def test_rejoin_rewinds_and_follows_the_address_on_its_own_slot(box):
    box.set("pg_up", "recovery", "wire_answers", "streams_after_start")     # a standby that has stopped streaming
    assert box.run("rejoin.sh") == 0, box.out
    calls = box.calls()
    assert "pg_rewind --target-pgdata" in calls and "host=10.0.0.10 port=5432 user=replicator dbname=postgres" in calls
    assert calls.index("stop postgresql") < calls.index("pg_rewind") < calls.index("systemctl start postgresql")
    auto = (box.pgdata / "postgresql.auto.conf").read_text()
    assert "host=10.0.0.2" not in auto and "stale" not in auto and "max_connections = 400" in auto
    assert "primary_conninfo = 'host=10.0.0.10 port=5432 user=replicator" in auto
    assert "primary_slot_name = 'node1_standby'" in auto
    assert (box.pgdata / "standby.signal").exists() and box.marker.exists()


def test_rejoin_refuses_a_standby_that_comes_up_without_streaming(box):
    box.set("pg_up", "recovery", "wire_answers")
    assert box.run("rejoin.sh") == 1
    assert "not streaming" in box.out


def test_rejoin_stops_at_a_refused_rewind_and_writes_nothing(box):
    box.set("pg_up", "wire_answers", "rewind_fails")
    assert box.run("rejoin.sh") == 1
    assert "full copy" in box.out
    assert (box.pgdata / "standby.signal").exists(), "a refused rewind must leave the box unstartable as a primary"
    assert "host=10.0.0.2" in (box.pgdata / "postgresql.auto.conf").read_text()


def test_fence_drops_the_address_before_it_stops_the_database_immediately(box):
    box.set("pg_up", "vip")
    assert box.run("fence.sh") == 0, box.out
    calls = box.calls()
    assert calls.index("ip addr del 10.0.0.10/24") < calls.index("kill -s SIGQUIT")
    assert not box.has("vip") and not box.has("pg_up") and box.marker.exists()
    assert "checkpoint" not in calls


def test_fence_reports_failure_while_the_database_still_runs(box):
    box.set("pg_up", "vip", "stop_hangs")
    assert box.run("fence.sh") == 1
    assert not box.has("vip")


def test_start_primary_refuses_a_box_that_was_a_standby(box):
    (box.pgdata / "standby.signal").touch()
    assert box.run("start-primary.sh") == 1
    assert "start postgresql" not in box.calls()


def test_start_primary_refuses_while_the_address_answers_elsewhere(box):
    box.set("wire_answers")
    assert box.run("start-primary.sh") == 1
    assert "start postgresql" not in box.calls()


def test_start_primary_starts_the_database_then_takes_the_address(box):
    box.marker.parent.mkdir(); box.marker.touch()
    assert box.run("start-primary.sh") == 0, box.out
    calls = box.calls()
    assert calls.index("systemctl start postgresql") < calls.index("ip addr add 10.0.0.10/24")
    assert box.has("vip") and not box.marker.exists()


def test_start_primary_refuses_a_database_that_comes_up_in_recovery(box):
    box.set("recovery")
    assert box.run("start-primary.sh") == 1
    assert not box.has("vip")
