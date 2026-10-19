"""The site shape's folder exists on main with its spec (plan step 4.4); the build fills it."""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_site_folder_carries_its_spec():
    spec = open(os.path.join(HERE, "spec.md"), encoding="utf-8").read()
    for line in ("owns:", "reads:", "publishes:", "outside check:", "jobs:"):
        assert line in spec, line
    assert "no deploy step" in spec and "8300" in spec
