"""The shipped `qv4-radiance` unit runs Radiance in the shape ruling 121
recorded (the integrator's experiment, 29 October 2026): both cards, their
render nodes passed one by one (rootless podman drops them when given the
whole /dev/dri), memlock unlimited for the pinned host pool, 10 slots (16 until 12 November 2026) at a
32k bound, the host pool and card headroom that leave the frozen product's
OCR server its room (hard limit 23), and the port on the loopback only."""
from __future__ import annotations

import pathlib
import shlex

UNIT = pathlib.Path(__file__).resolve().parents[1] / "units" / "qv4-radiance.service"


def _lines() -> list[str]:
    return UNIT.read_text(encoding="utf-8").splitlines()


def _env(box: str = None) -> dict:
    """The unit's Environment= defaults, then the box's own file over them (EnvironmentFile wins, as in systemd)."""
    env = {}
    for line in _lines():
        if line.startswith("Environment="):
            k, _, v = line[len("Environment="):].partition("=")
            env[k] = v
    own = UNIT.parent / f"qv4-radiance-{box}.env"
    if box and own.exists():
        for line in own.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _exec_start(box: str = None) -> list[str]:
    """ExecStart joined across its continuation lines, ${VAR} expanded for `box`, and split as systemd would."""
    text, out, on = UNIT.read_text(encoding="utf-8"), [], False
    for k, v in _env(box).items():
        text = text.replace("${" + k + "}", v)
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
    """The experiment's shape, but for the bound and the pool: 32k and 20 GiB a
    rank since 31 October (the bulk ingest: at 16k and 11 GiB the KV cache was
    22,652 tokens and three requests ran at a time; a bigger pool moves
    experts off-card and the KV cache takes the VRAM they leave: 524,396)."""
    argv = _exec_start()
    want = {"--tp": "2", "--max-num-seqs": "10", "--max-model-len": "32768", "--max-num-batched-tokens": "4096",
            "--draft-window": "adaptive", "--checkpoint-policy": "tip-only", "--ngram-placement": "ram",
            "--host-pool-mib": "11776", "--gpu-headroom-mib": "500", "--placement": "expert_tiered", "--vision-tower-placement": "ram",
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


def test_the_model_and_its_ngram_table_are_a_boxs_own_setting():
    """12 November 2026 (Arthur, "move it"): node2 reads the n-gram table from the model copy on its spare drive;
    every other box keeps the model on /home and the table in RAM. The file must be there before the container."""
    assert _flag(_exec_start("node1"), "--ngram-placement") == "ram"
    assert "/home/user/models/radiance/qwen3.8-next-flash-fp8-iq4r-moe.rad:/model.rad:ro" in _exec_start("node1")
    two = _exec_start("node2")
    assert _flag(two, "--ngram-placement") == "disk"
    assert "/mnt/ssd2/radiance/qwen3.8-next-flash-fp8-iq4r-moe.rad:/model.rad:ro" in two
    lines = _lines()
    assert "EnvironmentFile=-/home/user/querynzv4/support/scheduler/units/qv4-radiance-%H.env" in lines
    assert "ExecStartPre=/usr/bin/test -r ${QV4_RADIANCE_MODEL}" in lines
    assert lines.index("ExecStartPre=/usr/bin/test -r ${QV4_RADIANCE_MODEL}") < next(
        i for i, l in enumerate(lines) if l.startswith("ExecStart="))
