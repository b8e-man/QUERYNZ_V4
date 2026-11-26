"""The serving record (tranche 1 of the reader-configuration system, Arthur, 26 November 2026): what actually runs,
read from the installed units, the image by id and the weights by hash, as one id a reading carries."""
from __future__ import annotations

import json
import os

from support import reader as rd
from support.recipes import serving

UNIT = """[Unit]
Description=the proxy  # a comment is no part of the serving
Requires=qv4-x-card@0.service qv4-x-card@1.service
[Service]
Environment=QV4_MODEL_FILE=/m/w.rad OTHER_API_KEY=abc123
EnvironmentFile=-%h/.querynz/x-%H.env
ExecStart=/usr/bin/python -m proxy --backends a,b
"""
CARD = """[Service]
# card %i
Environment=QV4_W=/m/w.rad
ExecStart=/usr/bin/podman run --name x%i -e HIP_VISIBLE_DEVICES=%i \\
  -p 127.0.0.1:807%i:8000 -v ${QV4_W}:/model.rad:ro \\
  docker.io/example/radiance:latest --model /model.rad --max-num-seqs 8
"""


class Prof:
    name, model, binary, unit, cards, slots, context = "x", "m", "radiance", "qv4-x.service", 2, 16, 32768
    weights = ("w.rad",)
    standing = True


def units(tmp_path):
    (tmp_path / "qv4-x.service").write_text(UNIT)
    (tmp_path / "qv4-x-card@.service").write_text(CARD)
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "w.rad").write_bytes(b"weights")
    return tmp_path


def test_a_template_is_read_for_each_instance_and_its_variables_filled(tmp_path):
    rec = serving.unit_record("qv4-x-card@.service", str(units(tmp_path)), box="node2", instance="1")
    assert rec["unit"] == "qv4-x-card@1.service"
    run = next(l for l in rec["lines"] if l.startswith("ExecStart="))
    assert "--name x1" in run and "HIP_VISIBLE_DEVICES=1" in run and "127.0.0.1:8071:8000" in run
    assert "-v /m/w.rad:/model.rad:ro" in run, "${QV4_W} filled from the unit's own Environment="
    assert not any("card %i" in l or l.startswith("#") for l in rec["lines"]), "comments are no part of the serving"
    assert serving.images_of(rec) == ["docker.io/example/radiance:latest"]


def test_a_credential_never_reaches_the_record(tmp_path):
    rec = serving.unit_record("qv4-x.service", str(units(tmp_path)), box="node2")
    text = json.dumps(rec)
    assert "abc123" not in text and "OTHER_API_KEY=<withheld>" in text
    assert serving._fillable("QV4_MODEL_FILE") and not serving._fillable("QV4_API_TOKEN") and not serving._fillable("HOME")


def test_one_serving_has_one_id_on_both_boxes_and_a_changed_one_another(tmp_path):
    d = units(tmp_path)
    ledger = {("w.rad", 7): "f" * 64}
    def digest(image):
        return "sha256:abc"
    a = serving.standing(Prof, str(d), "node1", str(d / "models"), digest=digest, ledger=ledger)
    b = serving.standing(Prof, str(d), "node2", str(d / "models"), digest=digest, ledger=ledger)
    assert serving.serving_id(a) == serving.serving_id(b), "the box's name is no part of how the model is served"
    assert a["images"] == {"docker.io/example/radiance:latest": "sha256:abc"} and a["weights"][0]["sha256"] == "f" * 64
    (d / "qv4-x-card@.service").write_text(CARD.replace("--max-num-seqs 8", "--max-num-seqs 16"))
    c = serving.standing(Prof, str(d), "node1", str(d / "models"), digest=digest, ledger=ledger)
    assert serving.serving_id(c) != serving.serving_id(a), "a changed concurrency is another serving"


def test_weights_the_ledger_lacks_are_named_unhashed_never_passed(tmp_path):
    d = units(tmp_path)
    rec = serving.standing(Prof, str(d), "node2", str(d / "models"), digest=lambda i: None, ledger={})
    assert rec["weights"] == [{"file": "w.rad", "size": 7, "sha256": serving.UNHASHED}]
    assert rec["images"] == {"docker.io/example/radiance:latest": None}


def test_a_spawned_server_leaves_its_port_out(tmp_path):
    argv = ["/b/llama-server", "-m", "/m/w.rad", "--port", "8021", "-c", "8192"]
    one = serving.spawned(Prof, argv, "/b/llama-server", str(tmp_path), {}, program_sha=lambda p: "p" * 64)
    two = serving.spawned(Prof, argv[:4] + ["8022"] + argv[5:], "/b/llama-server", str(tmp_path), {}, program_sha=lambda p: "p" * 64)
    assert serving.serving_id(one) == serving.serving_id(two) and "<port>" in one["argv"]


def test_a_record_is_appended_once_and_resolves(tmp_path):
    led = str(tmp_path / "servings.jsonl")
    serving._RECORDED.clear()
    rec = {"kind": "standing", "profile": "x"}
    sid = serving.record(rec, led, box="node2")
    serving._RECORDED.clear()
    assert serving.record(rec, led, box="node1") == sid
    assert len(open(led).read().splitlines()) == 1, "append-only, one line an id"
    assert serving.resolve(sid, led)["record"] == rec


def test_a_reading_carries_the_serving_id_the_worker_gave_it(tmp_path, monkeypatch):
    monkeypatch.setenv("QV4_SERVING_ID", "98e5ddf6603eb834")
    store = rd.Store(str(tmp_path))
    r = rd.Reading(document="a" * 64, page=1, reader="t 1", model="m", settings={}, profile="p", profile_version=1,
                   read_from="text", text="x")
    store.put(r)
    assert store.get(r.key).serving == "98e5ddf6603eb834"
    monkeypatch.delenv("QV4_SERVING_ID")
    r2 = rd.Reading(document="b" * 64, page=1, reader="t 1", model="m", settings={}, profile="p", profile_version=1,
                    read_from="text", text="x")
    store.put(r2)
    assert store.get(r2.key).serving == "", "outside the worker nothing is claimed"


def test_the_manager_says_unmeasured_and_asks_again(tmp_path, monkeypatch):
    from support.scheduler import cards
    m = cards.Manager(ask=lambda p: {}, models_dir=str(tmp_path), reservations=[], window=None, schedule=None,
                      systemctl=lambda *a, **k: 0, read_cards=lambda: None)
    class W:
        box = "node2"
    calls = []
    def broken(prof, box=None, models_dir=None):
        calls.append(1)
        raise OSError("no unit file")
    monkeypatch.setattr(serving, "standing", broken)
    sid = m.serving_for(W, Prof, 8060)
    assert sid.startswith(serving.UNMEASURED) and "no unit file" in sid
    m.serving_for(W, Prof, 8060)
    assert len(calls) == 2, "an unmeasured serving is asked again, never kept as known"
    monkeypatch.setattr(serving, "standing", lambda prof, box=None, models_dir=None: {"kind": "standing", "p": 1})
    monkeypatch.setattr(serving, "LEDGER", str(tmp_path / "s.jsonl"))
    good = m.serving_for(W, Prof, 8060)
    assert good == serving.serving_id({"kind": "standing", "p": 1}) and m.serving_for(W, Prof, 8060) == good
