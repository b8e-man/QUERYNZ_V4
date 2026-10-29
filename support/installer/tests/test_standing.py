"""A standing service the repository ships is enabled by the installer, as
the worker's instance is: `qv4-radiance` (ruling 121) must come back on a
boot, and a unit placed but not enabled does not. Only a `qv4-` service
with an `[Install]` section is enabled; a template and a timer's service
are not, and nothing foreign is touched."""
from __future__ import annotations

from support import installer as inst
from support.installer.tests.test_installer import fake_repo


def test_a_standing_service_with_an_install_section_is_enabled_and_a_timers_service_is_not(tmp_path):
    repo = fake_repo(tmp_path)
    (tmp_path / "repo" / "support" / "scheduler" / "units" / "qv4-radiance.service").write_text(
        "[Service]\nExecStart=/usr/bin/podman run x\n\n[Install]\nWantedBy=default.target\n")
    units = tmp_path / "units"
    units.mkdir()
    calls = []
    inst.install_units(repo, str(units), box="node2", sh=lambda c: calls.append(c) or (0, ""))
    enabled = [c[-1] for c in calls if c[2] == "enable"]
    assert "qv4-radiance.service" in enabled, "a standing service is enabled, so a reboot brings it back"
    assert ["systemctl", "--user", "enable", "--now", "qv4-radiance.service"] in calls
    assert "qv4-a.service" not in enabled, "a timer's service has no [Install] and is never enabled"
    assert "qv4-worker@.service" not in enabled, "a template is enabled by its instance only"


def test_only_names_the_standing_service_it_places(tmp_path):
    repo = fake_repo(tmp_path)
    (tmp_path / "repo" / "support" / "scheduler" / "units" / "qv4-radiance.service").write_text(
        "[Service]\nExecStart=/bin/true\n\n[Install]\nWantedBy=default.target\n")
    units = tmp_path / "units"
    units.mkdir()
    calls = []
    inst.install_units(repo, str(units), box="node2", sh=lambda c: calls.append(c) or (0, ""), only=("qv4-a.timer",))
    assert "qv4-radiance.service" not in [c[-1] for c in calls], "a rehearsal of one unit enables nothing else"
    calls.clear()
    inst.install_units(repo, str(units), box="node2", sh=lambda c: calls.append(c) or (0, ""), only=("qv4-radiance.service",))
    assert [c[-1] for c in calls if c[2] == "enable"] == ["qv4-radiance.service"]


def test_the_standing_services_are_read_from_the_unit_text():
    assert inst.standing("[Unit]\n[Service]\nExecStart=x\n[Install]\nWantedBy=default.target\n")
    assert not inst.standing("[Service]\nExecStart=x\n")
    assert not inst.standing("[Service]\nExecStart=x\n# [Install]\n")
