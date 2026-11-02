"""Step 8.2's measurements (2 November 2026): which side of a declared entry's dash names the body, per category; the real
property category is never read."""
from links import measure


def test_the_body_is_read_from_the_side_its_category_puts_it():
    assert measure.declared_body("Te Karetu Farm Limited – agriculture", "before") == [("before", "Te Karetu Farm Limited")]
    assert measure.declared_body("Rugby World Cup tickets to semi-final – HSBC", "after") == [("after", "HSBC")]
    assert measure.declared_body("Simplicity Investment Growth Fund – Simplicity NZ Limited", "both") == [
        ("before", "Simplicity Investment Growth Fund"), ("after", "Simplicity NZ Limited")]
    assert measure.declared_body("PS Ardern Family Trust (trustee)", "whole") == [("before", "PS Ardern Family Trust")]
    assert measure.declared_body("Tickets to the match (x2)", "after") == [], "no dash: nothing after it"


def test_real_property_is_never_a_category_read():
    assert "real-property" not in measure.DECLARED_SIDES
    assert set(measure.READ_NOW) <= set(measure.DECLARED_SIDES)
