"""Two Parliamentary Service workbooks print every name surname first with no comma ("Seymour David"); checked against
the member roster on 1 November 2026 (77 of 123 match read that way, none given-first)."""
from types import SimpleNamespace as N

from registers.expenses import read as R


def test_a_table_with_no_comma_in_any_name_is_read_surname_first_with_particles_kept_in_the_surname():
    t = N(lines=[N(kind="member", name="Seymour David"), N(kind="member", name="van de Molen Tim"), N(kind="total", name="")])
    assert R.surname_first(t)
    assert [R.person(n, True) for n in ("Seymour David", "van de Molen Tim", "Bakshi Kanwaljit Singh", "Mallard Trevor (1) (2)")] == \
        ["David Seymour", "Tim van de Molen", "Kanwaljit Singh Bakshi", "Trevor Mallard"]


def test_a_table_that_prints_commas_is_read_as_before():
    t = N(lines=[N(kind="member", name="Hughes, Gareth"), N(kind="member", name="Seymour David")])
    assert not R.surname_first(t)
    assert R.person("Hughes, Gareth") == "Gareth Hughes" and R.person("Hughes, Gareth", True) == "Gareth Hughes"
    assert R.person("Seymour David") == "Seymour David", "given-first unless the table says otherwise"
