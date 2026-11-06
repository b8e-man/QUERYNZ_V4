"""`[boxes.<box>] only_profiles` in jobs.toml: node1 was limited to Flash-Next's views on 6 November 2026 and
lifted the same day, once it read node2's old folder over NFS (ruling 145: both boxes take every job)."""
from support.scheduler import registry as reg


def test_the_shipped_catalogue_limits_no_box():
    assert reg.box_only_profiles("node1") == frozenset()
    assert reg.box_only_profiles("node2") == frozenset()


def test_a_box_not_named_takes_every_job(tmp_path):
    j = tmp_path / "jobs.toml"
    j.write_text('[boxes.a]\nonly_profiles = ["x"]\n')
    assert reg.box_only_profiles("a", j) == {"x"} and reg.box_only_profiles("b", j) == frozenset()
    j.write_text("")
    assert reg.box_only_profiles("a", j) == frozenset()
