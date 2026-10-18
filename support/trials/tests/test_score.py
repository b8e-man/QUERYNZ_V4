"""The page scores: invented runs, loops, amounts to the cent, parts,
agreement; pure functions, no model, no file."""
from support.trials import score

KEY = """RETURN OF PARTY DONATIONS
Part A: Donations of more than $15,000
1  A Donor Trust   12/03/2023   $25,000.00
2  Another Giver   01/04/2023   $16,500.50
TOTAL FOR PART A   $41,500.50
"""


def test_a_faithful_reading_scores_clean():
    s = score.score_page(KEY, KEY)
    assert s["has_key"] and not s["invented_fail"] and not s["loop_fail"]
    assert s["amounts_exact"] and s["amounts_missing"] == 0 and s["amounts_extra"] == 0
    assert s["parts_found"] == "A" and s["parts_key"] == "A"
    assert s["amounts_key"] == 4 and s["amount_rows"] == 4


def test_five_invented_words_fail_the_page_and_four_do_not():
    four = KEY + "\nwords not on page\n"                 # four words: under the rule
    five = KEY + "\nfive words that are invented here\n"
    assert not score.score_page(four, KEY)["invented_fail"]
    s = score.score_page(five, KEY)
    assert s["invented_fail"] and s["invented_runs"] == 1 and s["invented_longest"] >= 5


def test_markup_is_not_content():
    html = "<div data-label='Table'><table><tr><td>1</td><td>A Donor Trust</td><td>$25,000.00</td></tr></table></div>"
    s = score.score_page(html, "1 A Donor Trust $25,000.00")
    assert not s["invented_fail"] and s["amounts_exact"]


def test_a_wrong_cent_is_a_missing_and_an_extra_amount():
    wrong = KEY.replace("$16,500.50", "$16,500.00")
    s = score.score_page(wrong, KEY)
    assert not s["amounts_exact"] and s["amounts_missing"] == 1 and s["amounts_extra"] == 1


def test_bare_integers_are_not_amounts():
    assert score.amounts("page 3 of 12 in 2023 row 1") == {}
    assert score.amounts("$1,500 and 2,000.00 and $30") == {150000: 1, 200000: 1, 3000: 1}


def test_a_loop_fails_the_page_but_a_genuinely_repeated_row_does_not():
    looped = KEY + "TOTAL FOR PART A   $41,500.50\nTOTAL FOR PART A   $41,500.50\n"
    assert score.score_page(looped, KEY)["loop_fail"]
    repeated_key = "3  Same Giver  $100.00\n3  Same Giver  $100.00\n3  Same Giver  $100.00\n"
    assert not score.score_page(repeated_key, repeated_key)["loop_fail"]


def test_without_a_key_loops_are_judged_against_the_other_readers_and_lone_amounts_counted():
    others = {"zhipu": KEY}
    mine = KEY + "9  Nobody Else Saw   $999.99\n"
    s = score.score_page(mine, None, others)
    assert not s["has_key"] and s["invented_fail"] is None
    assert s["amounts_lone"] == 1 and not s["loop_fail"]
    assert score.score_page(mine + "x y z\nx y z\nx y z\n", None, others)["loop_fail"]


def test_agreement_between_two_readers():
    a = score.agreement(KEY, KEY)
    assert a["agree"] and a["only_a"] == 0
    b = score.agreement(KEY, KEY.replace("$25,000.00", "$25,000.10"))
    assert not b["agree"] and b["only_a"] == 1 and b["only_b"] == 1


def test_example_names_are_spotted():
    assert score.example_names("1  John Smith  $1,500.00") == ["john smith"]
    assert score.example_names(KEY) == []
