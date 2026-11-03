"""The source lights read the board's registers from its catalogue as a
file (checks may not import products); this root test, which may import
both, holds the reading equal to the catalogue itself."""
from checks import source_lights as sl
from products.board import catalogue as cat


def test_every_register_on_the_board_is_read_from_its_catalogue():
    assert sl.registers() == [(r, p, True) for r, p in cat.REGISTERS] + [(r, p, False) for r, p in cat.NOT_HELD]
