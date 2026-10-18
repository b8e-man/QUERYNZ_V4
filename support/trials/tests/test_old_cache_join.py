"""Pass one's join to the old estate's readings works on real pages: the
same bytes rendered at the old 200 dots per inch hash to the old cache's
key; at 300 they do not. Needs the old folder; a few seconds."""
import os

import pytest

from support.trials import pageset, piece


@pytest.mark.skipif(not os.path.isdir(piece.OLD_CACHE) or not os.path.isdir(pageset.STAGING), reason="the old folder is not on this box")
def test_the_old_cache_joins_by_image_hash_at_200_dpi_only():
    at_200 = piece.old_cache_check(3, pages_per_doc=2, dpi=200, log=lambda *_: None)
    assert at_200.get("hit", 0) >= 5 and not at_200.get("miss") and not at_200.get("render-failed")
    at_300 = piece.old_cache_check(1, pages_per_doc=1, dpi=300, log=lambda *_: None)
    assert at_300 == {"miss": 1}
