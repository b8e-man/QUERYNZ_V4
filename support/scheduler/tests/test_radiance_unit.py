"""The shipped model-server units (Arthur, 26 November 2026: "let's switch everything to 3.8 27b", one server a card):
`qv4-radiance-card@` runs Radiance with Qwen 3.8 27B on card %i alone, both render nodes passed one by one
(rootless podman drops them when given the whole /dev/dri; one alone left Radiance on the processor), memlock
unlimited, 8 slots at a 32k bound, the card headroom that leaves the frozen product's OCR server its room (hard limit
23), its port on the loopback only; `qv4-radiance` is the proxy over the two on :8060 and holds them as its parts.
Until 26 November `qv4-radiance` itself ran Flash-Next across both cards (ruling 121)."""
from __future__ import annotations

import pathlib
import shlex

UNITS = pathlib.Path(__file__).resolve().parents[1] / "units"
UNIT = UNITS / "qv4-radiance-card@.service"
PROXY = UNITS / "qv4-radiance.service"


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


def _exec_start(box: str = None, card: int = 0) -> list[str]:
    """ExecStart joined across its continuation lines, ${VAR} expanded for `box`, and split as systemd would."""
    text, out, on = UNIT.read_text(encoding="utf-8"), [], False
    for k, v in _env(box).items():
        text = text.replace("${" + k + "}", v)
    text = text.replace("%i", str(card))
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
    assert "/home/user/models/radiance/qwen3.8-27b-mxfp4.rad:/model.rad:ro" in argv
    assert _flag(argv, "--model") == "/model.rad"


def test_the_recorded_serving_shape():
    """The trial's shape (26 November 2026): one card, 8 sequences (Arthur: "lets go with 8"), the 32k bound."""
    argv = _exec_start()
    want = {"--tp": "1", "--max-num-seqs": "8", "--max-model-len": "32768", "--gpu-headroom-mib": "500",
            "--kv-cache-dtype": "fp8", "--port": "8000", "--served-model-name": "qwen38-27b"}
    assert {k: _flag(argv, k) for k in want} == want


def test_each_server_has_its_own_card_by_both_render_nodes_and_never_the_whole_folder():
    for card in (0, 1):
        argv = _exec_start(card=card)
        devices = [argv[i + 1] for i, a in enumerate(argv) if a == "--device"]
        assert devices == ["/dev/kfd", "/dev/dri/renderD128", "/dev/dri/renderD129"]
        assert f"HIP_VISIBLE_DEVICES={card}" in argv
        assert _flag(argv, "--name") == f"qv4-radiance-card{card}"


def test_memlock_is_unlimited_in_the_unit_and_the_container():
    assert "LimitMEMLOCK=infinity" in _lines()
    assert _flag(_exec_start(), "--ulimit") == "memlock=-1:-1"


def test_each_port_is_published_on_the_loopback_only_and_the_proxy_spreads_over_both():
    for card in (0, 1):
        argv = _exec_start(card=card)
        published = [argv[i + 1] for i, a in enumerate(argv) if a in ("-p", "--publish")]
        assert published == [f"127.0.0.1:807{card}:8000"]
        assert "--network=host" not in argv and "host" != dict(zip(argv, argv[1:])).get("--network")
    proxy = PROXY.read_text(encoding="utf-8")
    assert "-m support.scheduler.fanout --port 8060 --backends http://127.0.0.1:8070,http://127.0.0.1:8071" in proxy


def test_the_proxy_holds_both_servers_as_its_parts_and_comes_back_on_a_boot():
    lines, proxy = _lines(), PROXY.read_text(encoding="utf-8").splitlines()
    assert "PartOf=qv4-radiance.service" in lines, "stopping the proxy (the night window, the watchdog) stops the servers"
    assert "Requires=qv4-radiance-card@0.service qv4-radiance-card@1.service" in proxy
    assert "After=qv4-radiance-card@0.service qv4-radiance-card@1.service" in proxy
    assert "WantedBy=default.target" in proxy
    for ls in (lines, proxy):
        assert any(l.startswith("Restart=") and l != "Restart=no" for l in ls)
        assert "StartLimitBurst=3" in ls, "a server that cannot start stops trying, rather than alarm every 30 s"
    argv = _exec_start()
    assert "--replace" in argv and "--rm" in argv, "a container left by a crash is replaced, never a name clash"


def test_it_never_names_the_frozen_products_units_or_program():
    for unit in (UNIT, PROXY):
        live = [l for l in unit.read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("#")]
        for foreign in ("querynz-agent-llm", "querynz-vision-ocr", "/home/user/llama.cpp", "Git Repos", "Conflicts="):
            assert not any(foreign in l for l in live), f"{unit.name} acts on {foreign!r}"


def test_the_model_file_is_a_boxs_own_setting_and_must_be_there_first():
    for box in ("node1", "node2"):
        assert "/home/user/models/radiance/qwen3.8-27b-mxfp4.rad:/model.rad:ro" in _exec_start(box)
    lines = _lines()
    assert "EnvironmentFile=-/home/user/querynzv4/support/scheduler/units/qv4-radiance-%H.env" in lines
    assert "ExecStartPre=/usr/bin/test -r ${QV4_RADIANCE_27B}" in lines
    assert lines.index("ExecStartPre=/usr/bin/test -r ${QV4_RADIANCE_27B}") < next(
        i for i, l in enumerate(lines) if l.startswith("ExecStart="))
