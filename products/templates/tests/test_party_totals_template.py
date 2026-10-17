"""Every template file in the folder holds its five things (plan 1.11 adds the first: party-totals)."""
import os

import products.templates as tp

FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_every_template_file_passes_the_contract():
    ts = tp.all_templates(FOLDER)
    assert [t.name for t in ts] == ["party-totals"]
    for t in ts:
        assert tp.validate(t) == [], t.name
        assert t.reads[0].table == "pub.party_return_totals"
