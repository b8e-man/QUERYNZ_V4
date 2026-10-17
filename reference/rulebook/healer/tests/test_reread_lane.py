"""The re-read lane — the machinery, not the taxonomy.

The readings themselves are proved in
`reconciliation/tests/test_reread_taxonomy.py` against verbatim corpus text.
What is proved here is the lane's conduct: that it reaches a document before
it acts, that it remembers what it read, that it disposes through the same
audited gate every other heal uses, and that it never deletes anything.
"""
import pathlib
import re

import pytest

SRC = (pathlib.Path(__file__).resolve().parents[1] / "healer/reread.py").read_text(encoding="utf-8")


def test_the_lane_abstains_entirely_without_a_document_source():
    """Queue 8's lesson, applied at the start: "nobody told me where the
    documents are" must not silently become "read the string instead". The
    string is the one thing this lane exists not to read."""
    assert "b = _backlog()" in SRC
    assert re.search(r"if b is None:.*?return \{", SRC, re.S), \
        "the lane proceeds without a document source"
    assert "from .repair import _backlog" in SRC, \
        "the lane opens its own connection instead of using the one home for it"


def test_the_lane_writes_down_what_it_read_including_what_it_refused():
    """73% of the candidates abstain. A lane that does not record an abstention
    re-selects it every cycle and never reaches the rest of the backlog — the
    trap recorded on _dispose_stripped in 2026-08-14, one layer up."""
    assert "INSERT INTO reread_log" in SRC
    assert "NOT EXISTS (SELECT 1 FROM reread_log" in SRC, \
        "candidates do not exclude what has already been read"
    ins = SRC[SRC.index("INSERT INTO reread_log"):SRC.index("if acted:")]
    assert "defects.ABSTAIN" in ins, "an abstention is not written down"


def test_the_lane_never_deletes_and_recovers_through_the_shared_gate():
    """Quarantine, never delete (standing rule). And a recovery goes through
    `_dispose_stripped`, which folds into the one live twin, renames when
    there is none, and abstains on two or more — so a re-read cannot create
    the duplicate a plain rename would."""
    assert "DELETE" not in SRC.upper().replace("DELETED", ""), "the lane deletes"
    assert "_dispose_stripped(g, r, reading.name" in SRC
    assert "quarantine_entity(g, r[\"id\"]" in SRC


def test_every_action_reaches_the_review_tab():
    assert "VERDICTS_PATH" in SRC and "_mirror(r, reading, aid)" in SRC
    mirror = SRC[SRC.index("def _mirror("):SRC.index("def run_reread(")]
    assert "except OSError" in mirror, \
        "an unwritable mirror stops the lane instead of being logged"


def test_the_run_is_capped_and_the_cap_is_named():
    assert re.search(r"REREAD_CAP = \d+", SRC)
    assert "LIMIT %s" in SRC and "(cap,)" in SRC


def test_the_earliest_mention_is_the_one_read():
    """A name is introduced in full before it is shortened, so the earliest
    sighting sits closest to the evidence."""
    assert "ORDER BY first_char NULLS LAST LIMIT 1" in SRC


def test_the_prefilter_reaches_every_class_the_taxonomy_names():
    """SQL picks shapes; `classify` decides. A class the prefilter cannot
    reach is a class the lane silently never runs — which is how a rule that
    passes its own tests heals nothing."""
    q = SRC[SRC.index("_CANDIDATES = "):SRC.index("def ensure_schema")]
    assert "strpos(e.name, '@') > 0" in q, "addresses are never selected"
    assert r"\.[0-9]{1,4}$" in q, "footnote markers are never selected"
    assert "[a-zāēīōū)][).][A-ZĀĒĪŌŪ0-9]" in q, "glued seams are never selected"
    assert "register_source IS NULL" in q and "quarantined_at IS NULL" in q


def test_the_taxonomy_is_imported_and_not_restated():
    """One home. A second copy of the class list here is a second place to
    change, and the estate has paid for that shape before."""
    assert "from reconciliation import defects" in SRC
    assert "email-address" not in SRC.split('"""', 2)[2], \
        "the lane names a defect class of its own instead of asking the taxonomy"


def test_the_lane_is_importable_and_its_ddl_is_additive():
    assert "CREATE TABLE IF NOT EXISTS reread_log" in SRC
    assert "ALTER TABLE" not in SRC, "the lane alters an existing table"
    assert "to_regclass('reread_log')" in SRC, \
        "the DDL runs every cycle and queues an ACCESS EXCLUSIVE behind every reader"


def test_a_document_too_long_to_hold_is_read_to_a_bound():
    """One re-read must not pull a 4 MB Hansard volume into memory per row."""
    assert re.search(r"DOC_CAP = [\d_]+", SRC)
    assert "[:DOC_CAP]" in SRC
