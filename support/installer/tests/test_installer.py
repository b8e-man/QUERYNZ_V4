"""The installer touches only `qv4-` units, reports a stale one and never
removes it, copies the model server beside the old build and never into
it, and knows which weights a profile needs."""
from __future__ import annotations

import os

import pytest

from support import installer as inst
from support.scheduler import registry as reg


def fake_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "checks" / "jobs").mkdir(parents=True)
    (repo / "support" / "scheduler" / "units").mkdir(parents=True)
    (repo / "checks" / "jobs" / "qv4-a.service").write_text("[Service]\nExecStart=/bin/true\n")
    (repo / "checks" / "jobs" / "qv4-a.timer").write_text("[Timer]\nOnCalendar=daily\n")
    (repo / "support" / "scheduler" / "units" / "qv4-worker@.service").write_text("[Service]\nExecStart=/bin/true\n")
    (repo / "requirements.txt").write_text("pytest>=8\n")
    return str(repo)


def test_only_prefixed_units_are_installed_and_a_stale_one_is_reported_not_removed(tmp_path):
    repo = fake_repo(tmp_path)
    units = tmp_path / "units"
    units.mkdir()
    (units / "ftm-release.service").write_text("the frozen product's\n")
    (units / "qv4-old.service").write_text("no longer shipped\n")
    (units / "qv4-a.service").write_text("an older copy\n")
    plan = {p["unit"]: p["action"] for p in inst.plan_units(repo, str(units))}
    assert plan == {"qv4-a.service": "update", "qv4-a.timer": "install", "qv4-worker@.service": "install", "qv4-old.service": "stale"}
    calls = []
    done = inst.install_units(repo, str(units), box="node2", sh=lambda c: calls.append(c) or (0, ""))
    assert {d["unit"] for d in done} == {"qv4-a.service", "qv4-a.timer", "qv4-worker@.service", "qv4-worker@node2.service"}
    assert (units / "ftm-release.service").read_text() == "the frozen product's\n"
    assert (units / "qv4-old.service").exists(), "stale is reported, never removed"
    assert (units / "qv4-a.service").read_text().startswith("[Service]")
    verbs = [tuple(c[2:4]) for c in calls]
    assert ("daemon-reload", "") not in verbs and any(c[2] == "daemon-reload" for c in calls)
    assert ("enable", "--now") in verbs
    enabled = [c[-1] for c in calls if c[2] == "enable"]
    assert enabled == ["qv4-a.timer", "qv4-worker@node2.service"]
    assert not any(c[2] in ("stop", "disable", "mask", "rm") for c in calls)
    assert all(not c[-1].startswith("ftm") for c in calls)


def test_a_unit_file_without_the_prefix_in_a_units_folder_is_refused(tmp_path):
    repo = fake_repo(tmp_path)
    open(os.path.join(repo, "checks", "jobs", "release.service"), "w").write("x")
    with pytest.raises(ValueError, match="hard limit 23"):
        inst.unit_sources(repo)


def test_the_model_server_is_copied_beside_never_over(tmp_path):
    src = tmp_path / "old" / "bin"
    src.mkdir(parents=True)
    (src / "llama-server").write_bytes(b"#!/bin/sh\necho 'version: 1 (abc123)'\n")
    os.chmod(src / "llama-server", 0o755)
    (src / "libggml.so.0").write_bytes(b"lib")
    os.symlink("libggml.so.0", src / "libggml.so")
    (src / "README").write_text("not copied")
    dst = tmp_path / "live" / "llama" / "bin"
    assert inst.plan_model_server(str(src), str(dst))["action"] == "install"
    got = inst.install_model_server(str(src), str(dst))
    assert got["action"] == "install" and got["version"] == "1 (abc123)" and got["copied"] == 3
    assert (dst / "VERSION.json").exists() and os.path.islink(dst / "libggml.so") and not (dst / "README").exists()
    assert sorted(os.listdir(src)) == ["README", "libggml.so", "libggml.so.0", "llama-server"], "the source is untouched"
    assert inst.plan_model_server(str(src), str(dst))["action"] == "same"
    (src / "llama-server").write_bytes(b"#!/bin/sh\necho 'version: 2 (def456)'\n")
    assert inst.plan_model_server(str(src), str(dst))["action"] == "update"


def test_the_profiles_weights_are_planned_by_file():
    plan = inst.plan_models(reg.profiles(), "/nowhere")
    planned = {p["profile"] for p in plan}
    profs = reg.profiles()
    assert planned == {n for n, p in profs.items() if not p.on}, "every profile with weights of its own is planned"
    assert {"flash-next", "embedding", "page-reader"} <= planned, \
        "the founding profiles are among them; the text reader and review are views on flash-next (ruling 121)"
    assert [p["file"] for p in plan if p["profile"] == "flash-next"] == ["/nowhere/radiance/qwen3.8-next-flash-fp8-iq4r-moe.rad"]
    assert all(p["present"] is False for p in plan if p["file"].startswith("/nowhere/")), "nothing is under /nowhere"
    assert all(p["file"].startswith("/nowhere/") for p in plan if not p["profile"].startswith("trial-")), \
        "the founding profiles' weights are relative to the models folder; only the trial's name the second disk"
    assert sum(1 for p in plan if p["profile"] == "page-reader") == 2, "the page reader has a projector too"


def test_the_shipped_units_all_carry_the_prefix():
    src = inst.unit_sources()
    assert "qv4-worker@.service" in src and all(n.startswith("qv4-") for n in src)


def test_a_timer_whose_job_is_on_the_queues_clock_is_superseded_not_enabled(tmp_path):
    """Step 2.12: the founding timers move into the catalogue; the installer
    disables and removes the timer, hands the clock over, keeps the service
    unit for a hand run, and never enables that timer again."""
    repo = fake_repo(tmp_path)
    (tmp_path / "repo" / "checks" / "jobs" / "qv4-b.service").write_text("[Service]\nExecStart=/bin/true\n")
    (tmp_path / "repo" / "checks" / "jobs" / "qv4-b.timer").write_text("[Timer]\nOnCalendar=daily\n")
    sched = tmp_path / "repo" / "support" / "scheduler"
    (sched / "jobs.toml").write_text('version = 1\n[jobs.qv4-b]\nneeds = "processor"\nmemory_gb = 0.1\ndeadline_s = 60\n'
                                     'query_timeout_s = 10\npriority = 1\ncommand = ["true"]\nat_utc = "18:30"\n')
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    (unit_dir / "qv4-b.timer").write_text("[Timer]\nOnCalendar=daily\n")      # the founding session's timer, live
    assert inst.timetabled_jobs(repo) == {"qv4-b"}
    plan = {p["unit"]: p["action"] for p in inst.plan_units(repo, str(unit_dir))}
    assert plan["qv4-b.timer"] == "superseded" and plan["qv4-b.service"] == "install" and plan["qv4-a.timer"] == "install"
    calls, handed = [], []
    done = inst.install_units(repo, str(unit_dir), box="node2", sh=lambda c, **k: (calls.append(c), (0, ""))[1],
                              handover=lambda job, timer: (handed.append((job, timer)), "2026-10-18 18:30+00")[1])
    assert ["systemctl", "--user", "disable", "--now", "qv4-b.timer"] in calls
    assert not (unit_dir / "qv4-b.timer").exists() and (unit_dir / "qv4-b.service").exists()
    assert handed == [("qv4-b", "qv4-b.timer")]
    assert [c[-1] for c in calls if c[2] == "enable"] == ["qv4-a.timer", "qv4-worker@node2.service"]
    assert {d["unit"]: d["action"] for d in done}["qv4-b.timer"] == "superseded"
    # a second install: nothing to disable, nothing to hand over, still never enabled
    calls.clear(); handed.clear()
    inst.install_units(repo, str(unit_dir), box="node2", sh=lambda c, **k: (calls.append(c), (0, ""))[1],
                       handover=lambda job, timer: handed.append((job, timer)))
    assert handed == [] and "qv4-b.timer" not in [c[-1] for c in calls]


def test_a_products_unit_folder_is_reached_and_its_prefix_is_enforced(tmp_path):
    """board-1: a product's surface ships its standing unit under products/<shape>/units/."""
    from support import installer
    repo = tmp_path / "repo"
    (repo / "products" / "board" / "units").mkdir(parents=True)
    (repo / "products" / "board" / "units" / "qv4-board.service").write_text("[Service]\nExecStart=/bin/true\n")
    assert "qv4-board.service" in installer.unit_sources(str(repo))
    (repo / "products" / "board" / "units" / "board.service").write_text("no prefix\n")
    try:
        installer.unit_sources(str(repo))
    except ValueError as e:
        assert "hard limit 23" in str(e)
    else:
        raise AssertionError("an unprefixed unit in a product folder must be refused")



def test_the_shipped_worker_unit_runs_from_the_release_copy_never_the_main_checkout():
    """Card the-scheduler-s-worker-runs-the-main-checkout-…, finding 2: the
    worker and every job it starts run the release copy."""
    text = open(inst.unit_sources()["qv4-worker@.service"], encoding="utf-8").read()
    lines = text.splitlines()
    assert "WorkingDirectory=/home/user/querynzv4-release" in lines
    assert any(l.startswith("ExecStart=/home/user/querynzv4-release/.venv/bin/python -m support.scheduler worker") for l in lines)
    assert not any(l.startswith(("WorkingDirectory=/home/user/querynzv4/", "ExecStart=/home/user/querynzv4/"))
                   or l == "WorkingDirectory=/home/user/querynzv4" for l in lines)


def release_repo(tmp_path, monkeypatch):
    repo = fake_repo(tmp_path)
    copy = tmp_path / "release"
    monkeypatch.setattr(inst, "RELEASE_COPY", str(copy))
    worker = os.path.join(repo, "support", "scheduler", "units", "qv4-worker@.service")
    open(worker, "w").write(f"[Service]\nWorkingDirectory={copy}\nExecStart={copy}/.venv/bin/python -m support.scheduler worker\n")
    return repo, copy


def test_the_worker_unit_is_refused_until_the_release_copy_exists(tmp_path, monkeypatch):
    repo, copy = release_repo(tmp_path, monkeypatch)
    monkeypatch.setattr(inst, "MAIN_CHECKOUT", repo)      # the integrator's install: from the main checkout, shipped text
    units = tmp_path / "units"
    units.mkdir()
    (units / "qv4-worker@.service").write_text("the unit running now\n")
    calls = []
    sh = lambda c: calls.append(c) or (0, "")  # noqa: E731
    done = {d["unit"]: d for d in inst.install_units(repo, str(units), box="node2", sh=sh)}
    assert done["qv4-worker@.service"]["action"] == "refused" and "not made" in done["qv4-worker@.service"]["why"]
    assert (units / "qv4-worker@.service").read_text() == "the unit running now\n", "the unit on the box is left as it is"
    assert "qv4-worker@node2.service" not in [c[-1] for c in calls], "a worker without its copy is never enabled"
    assert done["qv4-a.timer"]["action"] == "install", "every other unit is still placed"
    (copy / ".git").mkdir(parents=True)
    (copy / ".git" / "qv4-release.json").write_text('{"commit": "abc"}')
    done = {d["unit"]: d for d in inst.install_units(repo, str(units), box="node2", sh=sh)}
    assert "no .venv" in done["qv4-worker@.service"]["why"]
    (copy / ".venv" / "bin").mkdir(parents=True)
    (copy / ".venv" / "bin" / "python").write_text("")
    calls.clear()
    done = {d["unit"]: d for d in inst.install_units(repo, str(units), box="node2", sh=sh)}
    assert done["qv4-worker@.service"]["action"] == "update" and done["qv4-worker@node2.service"]["action"] == "enabled"
    assert f"WorkingDirectory={copy}\n" in (units / "qv4-worker@.service").read_text()
    assert ["systemctl", "--user", "enable", "--now", "qv4-worker@node2.service"] in calls


def test_a_rehearsal_from_a_working_copy_rewrites_the_release_path_and_the_release_copy_installs_the_shipped_text(
        tmp_path, monkeypatch):
    repo, copy = release_repo(tmp_path, monkeypatch)
    src = os.path.join(repo, "support", "scheduler", "units", "qv4-worker@.service")
    text = inst.unit_text(src, repo)
    assert f"WorkingDirectory={os.path.realpath(repo)}\n" in text and "REHEARSAL" in text
    assert f"ExecStart={inst.MAIN_CHECKOUT}/.venv/bin/python -m" in text, "a working copy without a .venv uses the main one"
    assert inst.release_missing(text) is None, "a rehearsal does not wait on the release copy"
    copy.mkdir()
    assert inst.unit_text(src, str(copy)) == open(src).read(), "installed from the release copy: the shipped text"
    main_unit = tmp_path / "m.service"
    main_unit.write_text(f"[Service]\nWorkingDirectory={inst.MAIN_CHECKOUT}\n")
    assert f"WorkingDirectory={os.path.realpath(repo)}\n" in inst.unit_text(str(main_unit), repo)
