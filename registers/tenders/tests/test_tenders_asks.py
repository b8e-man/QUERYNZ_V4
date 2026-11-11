"""The tenders lane's request to the provider (11 November 2026): every GETS file is asked until the MCP serves
estate-tenders; after that, only a current file held past REFRESH_DAYS, or a file never held."""
import datetime as dt
import json

from registers.tenders import asks

NOW = dt.datetime(2026, 11, 11, tzinfo=dt.timezone.utc)
AUG = dt.datetime(2026, 8, 14, tzinfo=dt.timezone.utc)


class _Conn:
    def __init__(self, held, copied):
        self.held, self.copied = held, copied

    def execute(self, q, params=None):
        rows = [(1 if self.copied else 0,)] if "mcpsource.cursors" in q else self.held
        return type("C", (), {"fetchall": lambda s: rows, "fetchone": lambda s: rows[0]})()


def _held(at):
    return [(n, "ab" * 32, at) for n in asks.CURRENT + asks.STATIC]


def test_every_file_is_asked_until_the_provider_holds_the_corpus(tmp_path):
    s = asks.short(_Conn(_held(AUG), copied=False), now=NOW)
    assert s["missing"] == 9 and all(f["wanted"] for f in s["files"]) and s["request_id"] == "estate-tenders@files-9-held-2026-08-14"
    out = asks.write(_Conn(_held(AUG), copied=False), path=str(tmp_path / "tenders.json"), now=NOW)
    on_disk = json.loads((tmp_path / "tenders.json").read_text())
    assert out["missing"] == 9 and on_disk["corpus"] == "estate-tenders" and "row" not in json.dumps(on_disk["files"])


def test_once_copied_only_a_stale_current_file_or_one_never_held_is_asked():
    assert asks.short(_Conn(_held(AUG), copied=True), now=NOW)["missing"] == 0          # 89 days: fresh
    late = asks.short(_Conn(_held(AUG), copied=True), now=AUG + dt.timedelta(days=121))
    assert {f["file"] for f in late["files"] if f["wanted"]} == set(asks.CURRENT)       # historic files never go stale
    some = asks.short(_Conn(_held(AUG)[1:], copied=True), now=NOW)
    assert [f["file"] for f in some["files"] if f["wanted"]] == [asks.CURRENT[0]]       # one never held
