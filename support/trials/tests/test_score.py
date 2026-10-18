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
    four = KEY + "\nwords never seen here\n"             # four words: under the rule
    five = KEY + "\nfive strange words were invented here\n"
    assert not score.score_page(four, KEY)["invented_fail"]
    s = score.score_page(five, KEY)
    assert s["invented_fail"] and s["invented_runs"] == 1 and s["invented_longest"] >= 5


def test_page_words_out_of_order_are_not_invention():
    scrambled = "Giver Another 01/04/2023 $16,500.50 Trust Donor A 12/03/2023 $25,000.00 PART A TOTAL FOR $41,500.50 Part A Donations of"
    s = score.score_page(scrambled, KEY)
    assert not s["invented_fail"] and s["invented_runs"] == 0


def test_the_key_may_come_in_two_orderings():
    raw = "RETURN OF PARTY DONATIONS Part A: Donations of more than $15,000 TOTAL FOR PART A $41,500.50"
    reading = "RETURN OF PARTY DONATIONS\nTOTAL FOR PART A $41,500.50\nnew words that nobody printed anywhere\n"
    s = score.score_page(reading, [KEY, raw])
    assert s["invented_fail"] and s["invented_runs"] == 1


def test_a_run_on_a_partial_key_is_undecided_until_another_family_reads_it():
    reading = KEY + "\nSecretary typed value in a field\n"
    alone = score.score_page(reading, KEY, {}, key_partial="form fields")
    assert alone["invented_fail"] is None and alone["invented_runs"] == 1 and alone["key_partial"] == "form fields"
    confirmed = score.score_page(reading, KEY, {"qwen": reading}, key_partial="form fields")
    assert confirmed["invented_fail"] is False and confirmed["key_lacked"] == 1 and confirmed["invented_runs"] == 0
    denied = score.score_page(reading, KEY, {"qwen": KEY}, key_partial="form fields")
    assert denied["invented_fail"] is True


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


def test_a_loop_inside_one_line_fails_the_page():
    sideways = KEY + "| " + "$0.00 | " * 15 + "\n"
    assert score.score_page(sideways, KEY)["loop_fail"]
    wide_row = KEY + "| " + "$0.00 | " * 8 + "\n"          # a wide table row is not a loop
    assert not score.score_page(wide_row, KEY)["loop_fail"]
    assert not score.score_page(sideways, sideways)["loop_fail"]    # the key shows the same line


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


def test_example_names_are_names_not_the_word_example():
    assert score.example_names("1  John Smith  $1,500.00") == ["john smith"]
    assert score.example_names("for example, a donation received in two parts; a sample return") == []
    assert score.example_names(KEY) == []
    assert score.example_names("1  John Smith  $1,500.00", key="example: John Smith $1,500.00") == []


def test_fonts_of_a_scanner_layer_are_recognised():
    assert score.OCR_FONT.match("CIDFont+F1") and score.OCR_FONT.match("*Verdana-Bold-11407-Identity")
    assert not score.OCR_FONT.match("Helvetica") and not score.OCR_FONT.match("Century")
