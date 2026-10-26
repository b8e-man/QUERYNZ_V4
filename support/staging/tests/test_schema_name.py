"""The staging schema's name leaves room for the lane's private schema."""
from support import staging


def test_a_long_branch_and_module_still_fit_with_the_private_suffix():
    name = staging.staging_schema("integrate/diaries-parliament", "registers/ministers_diaries")
    assert len(name) + len(staging.PRIVATE_SUFFIX) <= 63
    assert name.startswith("staging_integrate_diaries_parliament_registers_")
    assert name + staging.PRIVATE_SUFFIX != (name + staging.PRIVATE_SUFFIX)[:63] or len(name) + 8 <= 63


def test_two_lanes_of_one_branch_never_share_a_private_schema():
    a = staging.staging_schema("integrate/diaries-parliament", "registers/ministers_diaries")
    b = staging.staging_schema("integrate/diaries-parliament", "registers/parliament")
    assert a != b and (a + "_private")[:63] != a and (b + "_private")[:63] != b


def test_a_short_name_is_unchanged():
    assert staging.staging_schema("session/x", "registers/y") == "staging_session_x_registers_y"
