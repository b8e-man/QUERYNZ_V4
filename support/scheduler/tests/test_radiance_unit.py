"""The shipped `qv4-radiance` unit runs Radiance in the shape ruling 121
recorded (the integrator's experiment, 29 October 2026): both cards, their
render nodes passed one by one (rootless podman drops them when given the
whole /dev/dri), memlock unlimited for the pinned host pool, 16 slots at a
16k bound, the host pool and card headroom that leave the frozen product's
OCR server its room (hard limit 23), and the port on the loopback only."""
from __future__ import annotations

import pathlib
import shlex

UNIT = pathlib.Path(__file__).resolve().parents[1] / "units" / "qv4-radiance.service"


def _lines() -> list[str]:
    return UNIT.read_text(encoding="utf-8").splitlines()


def _exec_start() -> list[str]:
    """ExecStart joined across its continuation lines and split as systemd would."""
    text, out, on = UNIT.read_text(encoding="utf-8"), [], False
    for line in text.splitlines():
        if line.startswith("ExecStart="):
            on, line = True, line[len("ExecStart="):]
        if on:
            if line.lstrip().startswith("#"):
                continue
            out.append(line.rstrip("\\").strip())
            if not line.endswith("\\"):
                break
    return shlex.split(" ".join(out))


def _flag(argv: list[str], name: str) -> str:
    assert name in argv, f"{name} missing from the server's command"
    return argv[argv.index(name) + 1]


def test_the_unit_runs_the_recorded_image_and_model_read_only():
    argv = _exec_start()
    assert argv[:2] == ["/usr/bin/podman", "run"]
    assert "docker.io/stilldeadcode/radiance:latest" in argv
    assert "/home/user/models/radiance/qwen3.8-next-flash-fp8-iq4r-moe.rad:/model.rad:ro" in argv
    assert _flag(argv, "--model") == "/model.rad"


def test_the_recorded_serving_shape():
    """The experiment's shape, but for the pool: 11 GiB a rank, because at 10
    the server started after the OCR server ran out of card memory."""
    argv = _exec_start()
    want = {"--tp": "2", "--max-num-seqs": "16", "--max-model-len": "16384", "--max-num-batched-tokens": "4096",
            "--draft-window": "adaptive", "--checkpoint-policy": "tip-only", "--ngram-placement": "disk",
            "--host-pool-mib": "11264", "--gpu-headroom-mib": "2560", "--placement": "expert_tiered",
            "--kv-cache-dtype": "fp8", "--port": "8060", "--served-model-name": "qwen4exp"}
    assert {k: _flag(argv, k) for k in want} == want


def test_both_cards_by_their_render_nodes_one_by_one_and_never_the_whole_folder():
    argv = _exec_start()
    devices = [argv[i + 1] for i, a in enumerate(argv) if a == "--device"]
    assert devices == ["/dev/kfd", "/dev/dri/renderD128", "/dev/dri/renderD129"]
    assert "/dev/dri" not in devices
    assert "HIP_VISIBLE_DEVICES=0,1" in argv


def test_memlock_is_unlimited_in_the_unit_and_the_container():
    assert "LimitMEMLOCK=infinity" in _lines()
    argv = _exec_start()
    assert _flag(argv, "--ulimit") == "memlock=-1:-1"


def test_the_port_is_published_on_the_loopback_only():
    argv = _exec_start()
    published = [argv[i + 1] for i, a in enumerate(argv) if a in ("-p", "--publish")]
    assert published == ["127.0.0.1:8060:8060"]
    assert "--network=host" not in argv and "host" != dict(zip(argv, argv[1:])).get("--network")


def test_it_comes_back_on_a_boot_and_after_a_failure():
    lines = _lines()
    assert "WantedBy=default.target" in lines
    assert any(l.startswith("Restart=") and l != "Restart=no" for l in lines)
    argv = _exec_start()
    assert "--replace" in argv and "--rm" in argv, "a container left by a crash is replaced, never a name clash"
    assert "StartLimitBurst=3" in lines, "a server that cannot start stops trying, rather than alarm every 30 s"


def test_it_never_names_the_frozen_products_units_or_program():
    live = [l for l in _lines() if not l.lstrip().startswith("#")]
    for foreign in ("querynz-agent-llm", "querynz-vision-ocr", "/home/user/llama.cpp", "Git Repos", "Conflicts="):
        assert not any(foreign in l for l in live), f"the unit acts on {foreign!r}"
