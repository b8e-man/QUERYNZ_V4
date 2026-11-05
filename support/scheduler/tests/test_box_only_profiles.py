"""`[boxes.<box>] only_profiles` in jobs.toml (6 November 2026): node1 reads with its own Flash-Next and nothing else."""
from support.scheduler import registry as reg


def test_the_shipped_catalogue_limits_node1_to_flash_next_views_and_leaves_node2_whole():
    assert reg.box_only_profiles("node1") == {"text-reader", "review"}
    assert reg.box_only_profiles("node2") == frozenset()
    profiles = reg.profiles()
    assert all(p in profiles for p in reg.box_only_profiles("node1")), "every named profile exists"
    standing = {reg.server_of(profiles, p).name for p in reg.box_only_profiles("node1")}
    assert standing == {"flash-next"}, "node1's two profiles are views on its own standing server"


def test_a_box_not_named_takes_every_job(tmp_path):
    j = tmp_path / "jobs.toml"
    j.write_text('[boxes.a]\nonly_profiles = ["x"]\n')
    assert reg.box_only_profiles("a", j) == {"x"} and reg.box_only_profiles("b", j) == frozenset()
    j.write_text("")
    assert reg.box_only_profiles("a", j) == frozenset()
