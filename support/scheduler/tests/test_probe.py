"""The probe must not report a guess as a fact (carried from
ops/fleet/tests/test_probe.py: a failed probe is not an empty fleet, busy is
not down, could-not-ask is not disagrees), and the hardware profile must
hold the programs, because that is what node1 lacked."""
from __future__ import annotations

import json
import os
import shutil

import pytest

from support.scheduler import probe

ROCM = json.dumps({"card0": {"VRAM Total Memory (B)": "34208743424", "VRAM Total Used Memory (B)": "28550766592",
                             "Card Series": "AMD Radeon AI PRO R9700"},
                   "card1": {"VRAM Total Memory (B)": "34208743424", "VRAM Total Used Memory (B)": "1925365760",
                             "Card Series": "AMD Radeon AI PRO R9700"},
                   "system": {"Driver version": "x"}})


def test_cards_are_read_from_rocm_smi_with_their_memory():
    got = probe.cards(ROCM)
    assert [c["index"] for c in got] == [0, 1]
    assert got[0]["memory_total_gb"] == 31.9 and got[0]["memory_used_gb"] == 26.6
    assert got[1]["memory_used_gb"] == 1.8 and got[1]["product"] == "AMD Radeon AI PRO R9700"


def test_a_failed_probe_is_none_not_an_empty_box():
    """An ssh timeout was once about to be reported as 'node1 has no GPUs'."""
    assert probe.cards(run=lambda cmd: None) is None
    assert probe.cards("not json") is None
    assert probe.cards("null") is None


def test_memory_is_total_and_available_from_meminfo():
    text = "MemTotal:       131072000 kB\nMemFree:        9000000 kB\nMemAvailable:   107000000 kB\nSwapTotal: 41943040 kB\nSwapFree: 41943040 kB\n"
    got = probe.meminfo(text)
    assert got == {"memory_total_gb": 125.0, "memory_available_gb": 102.0, "swap_total_gb": 40.0, "swap_free_gb": 40.0}


def test_pressure_reads_the_kernels_figures():
    got = probe.pressure("some avg10=0.00 avg60=0.12 avg300=0.05 total=1\nfull avg10=0.00 avg60=0.00 avg300=0.00 total=0\n")
    assert got["some"]["avg60"] == 0.12 and got["full"]["avg10"] == 0.0


def test_disks_are_real_filesystems_with_free_space():
    mounts = ("proc /proc proc rw 0 0\n/dev/nvme0n1p3 / btrfs rw 0 0\n/dev/sda1 /mnt/hdd ntfs3 rw 0 0\n"
              "/dev/sda1 /mnt/hdd ntfs3 rw 0 0\ntmpfs /tmp tmpfs rw 0 0\n/dev/sdb1 /mnt/with\\040space ext4 rw 0 0\n")

    class U:
        def __init__(self, t, f):
            self.total, self.free = t, f

    got = probe.disks(mounts, usage=lambda m: U(4 * 1024 ** 4, 1024 ** 4) if "mnt" in m else U(2 * 1024 ** 4, 1024 ** 4))
    assert [d["mount"] for d in got] == ["/", "/mnt/hdd", "/mnt/with space"]
    assert got[1]["free_gb"] == 1024 and got[0]["total_gb"] == 2048


def test_programs_are_recorded_present_or_absent_and_matched_against_requires():
    got = probe.programs(("pdftotext", "ghost"), which=lambda n: "/usr/bin/pdftotext" if n == "pdftotext" else None)
    assert got == {"pdftotext": "/usr/bin/pdftotext", "ghost": None}
    assert probe.missing_programs({"programs": got}, ("pdftotext", "ghost", "other")) == ["ghost", "other"]


def test_every_program_the_catalogue_requires_is_one_the_probe_looks_for():
    """A requirement the probe never looks for reads as missing, so the job
    is never eligible and the worker says nothing (19 October: `zstd` held
    the off-site copy and its rehearsal on the queue). The per-profile model
    servers (`qv4-llama-server-<profile>`) are the open scheduler card."""
    from support.scheduler import registry as reg
    required = {r for jt in reg.load().values() for r in jt.requires if not r.startswith("qv4-llama-server-")}
    assert required <= set(probe.PROGRAMS), sorted(required - set(probe.PROGRAMS))


# ── a model server, asked (carried) ──────────────────────────────────────────

def test_the_served_model_is_read_from_the_servers_own_answer():
    assert probe.served_model('{"models": [{"name": "qwen3.6-35b-a3b-q4km"}]}') == "qwen3.6-35b-a3b-q4km"
    assert probe.served_model('{"data": [{"id": "glm-ocr"}]}') == "glm-ocr"
    assert probe.served_model("null") is None and probe.served_model("{") is None and probe.served_model("") is None


def test_busy_is_not_down():
    busy = json.dumps([{"id": 0, "is_processing": True}, {"id": 1, "is_processing": True}])
    assert probe.free_slots(busy) == (0, 2)
    assert probe.free_slots(None) == (-1, 0)
    assert probe.free_slots(json.dumps([{"is_processing": False}, {"is_processing": True}])) == (1, 2)


def test_only_the_instances_that_run_are_counted():
    listing = "  querynz-agent-llm.service loaded active running x\n  qv4-worker@.service loaded active running t\n* querynz-embed.service loaded failed failed y\n"
    assert probe.running_instances(listing) == ["querynz-agent-llm", "querynz-embed"]


def test_ask_server_combines_the_three_answers():
    def getter(url):
        if url.endswith("/v1/models"):
            return '{"models": [{"name": "m"}]}'
        if url.endswith("/slots"):
            return '[{"is_processing": false}]'
        return "ok"
    assert probe.ask_server(8111, getter) == {"port": 8111, "served": "m", "free": 1, "total": 1, "healthy": True}
    assert probe.ask_server(8111, lambda u: None) == {"port": 8111, "served": None, "free": -1, "total": 0, "healthy": False}


def test_get_refuses_anything_but_the_loopback():
    assert probe.get("http://10.0.0.2:8020/v1/models") is None


# ── the real box ─────────────────────────────────────────────────────────────

@pytest.mark.skipif(not shutil.which("rocm-smi"), reason="no rocm-smi here")
def test_the_real_profile_of_this_box_holds_cards_and_programs():
    """On node2: two cards, the processor count, the programs list with the
    old model server present. Not a measurement, a shape."""
    p = probe.profile("node2")
    assert p["cores"] >= 2 and p["memory_total_gb"] > 1
    assert p["cards"] is not None and len(p["cards"]) >= 1
    assert all(c["memory_total_gb"] for c in p["cards"])
    assert set(p["programs"]) == set(probe.PROGRAMS)
    assert any(d["mount"] == "/" for d in p["disks"])
    assert os.path.exists(p["programs"]["pdftotext"] or "/nonexistent") or p["programs"]["pdftotext"] is None
