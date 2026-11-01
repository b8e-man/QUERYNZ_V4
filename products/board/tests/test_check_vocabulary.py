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
    # a law's title a text reader filed among the people is no name (2 November 2026: six Hansard rows)
    assert not check.carries_residence("Retirement Villages (Retirement Village Residents) Amendment Bill")
    assert not check.carries_residence("Retirement Villages (Retirement Village Residents) Amendment Act 2018")
    assert not check.carries_residence("Superannuation (New Zealand Superannuation and Retirement Income) Bill")
    # a person named Bill is still a person
    assert check.carries_residence("Bill Doe (c/- Kowhai Retirement Village)")
    assert check.carries_residence("DOE, Bill (Sunrise Rest Home)")
    assert check.carries_residence("DOE (c/- Sunrise Rest Home), Bill"), "an inverted name ending in Bill is no title: the comma"
