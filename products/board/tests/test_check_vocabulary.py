"""The check's residence vocabulary is the comparison's (checks/comparison.py
RESIDENCE_WORDS): products may not import checks/ (imports run one way), so
it is copied and held equal here by reading the file."""
import os
import re

from products.board import check


def test_the_check_s_residence_vocabulary_is_the_comparison_s():
    src = open(os.path.join(os.path.dirname(check.__file__), "..", "..", "checks", "comparison.py"), encoding="utf-8").read()
    m = re.search(r"^RESIDENCE_WORDS = (\(.*?\))$", src, re.M | re.S)
    assert m, "checks/comparison.py has no RESIDENCE_WORDS tuple"
    assert tuple(eval(m.group(1))) == check.RESIDENCE_WORDS


def test_a_residence_after_a_person_s_name_is_caught_and_an_institution_is_not():
    assert check.carries_residence("Jane Doe, Sunrise Rest Home")
    assert check.carries_residence("Jane Doe (c/- Kowhai Retirement Village)")
    assert not check.carries_residence("Waimate & District Community Rest Home")
    assert not check.carries_residence("Sunrise Care Group Limited, Kowhai Rest Home")
    assert not check.carries_residence("Jane Doe")
