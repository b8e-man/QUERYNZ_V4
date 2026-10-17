"""C308 — a finder named for one format silently excludes the class that needs
reading most (#3603e8).

Measured over `var/staging/ec-donations` on 2026-10-09: 3,597 documents have a
stored read, 3,586 have a PDF, and the other **11 are held only as `.jpg`** —
all disclosures. `find_pdf` returned None for every one and `targets()` kept only
what it found, so the photographed forms — the readings actually in dispute
across C308 and C544 — were not even candidates.
"""
import pytest

# walks the old folder's staging tree: not for the fast tier
pytestmark = pytest.mark.slow
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]

from support.docread import sources as S          # noqa: E402


def test_a_raster_only_document_is_found():
    """The live class, from the tree rather than from a fixture."""
    jpgs = [p for p in S.STAGING.rglob("*.jpg") if p.is_file()]
    assert jpgs, "no photographed documents in staging — this test has nothing to prove"
    orphans = [p for p in jpgs if not p.with_suffix(".pdf").exists()]
    assert orphans, "every .jpg now has a .pdf beside it; re-measure before deleting this"
    for p in orphans:
        got = S.find_document(p.stem)
        assert got is not None, f"{p.name} is in staging and the finder cannot see it"
        assert got.suffix.lower() == ".jpg", got


def test_a_pdf_still_wins_when_both_are_stored():
    """Preference, not permission: the PDF carries page structure."""
    both = [p for p in S.STAGING.rglob("*.jpg")
            if p.is_file() and p.with_suffix(".pdf").exists()]
    for p in both[:5]:
        assert S.find_document(p.stem).suffix == ".pdf"


def test_the_stored_read_is_not_a_document():
    """`pageread/<dir>/<stem>.json` IS the read. A finder that returned it
    would feed a reader its own previous answer."""
    assert ".json" not in S.READABLE
    reads = sorted((S.STAGING / "pageread").rglob("*.json"))
    assert reads, "no stored reads"
    got = S.find_document(reads[0].stem)
    assert got is None or got.suffix.lower() != ".json"


def test_a_raster_is_told_from_a_paged_document():
    assert S.is_raster("x.jpg") and S.is_raster(pathlib.Path("a/b.PNG"))
    assert not S.is_raster("x.pdf")
    assert S.RASTER and ".pdf" not in S.RASTER


def test_no_format_is_readable_without_being_preferred_or_rastered():
    """The two constants cannot drift apart: anything readable is either the
    paged format or a raster, and a new entry must land in one."""
    assert set(S.READABLE) - S.RASTER == {".pdf"}


def test_the_suffix_is_matched_WITHOUT_CASE():
    """AND THE SAME LINE EXCLUDED A PDF. `rglob(f"{stem}.pdf")` is
    case-sensitive on this filesystem, so `residue/donations_20k/AOTEAR1.PDF`
    was invisible too — 3,585 targets became 3,597: eleven rasters and one
    shouted extension. Measured 2026-10-09, not reasoned about."""
    shouted = [p for p in S.STAGING.rglob("*.PDF") if p.is_file()]
    assert shouted, "no upper-case extensions left in staging — re-measure"
    for p in shouted:
        assert S.find_document(p.stem) is not None, p


def test_every_stored_read_now_has_its_document():
    """The whole point, as a census rather than an example: a stored read with
    no findable document is a document the readers cannot be pointed at."""
    missing = []
    for d in sorted((S.STAGING / "pageread").iterdir()):
        if not d.is_dir() or d.name.startswith("disclosures-quarantine"):
            continue
        for j in sorted(d.glob("*.json")):
            if S.find_document(j.stem) is None:
                missing.append(j.stem)
    assert not missing, f"{len(missing)} stored reads with no document: {missing[:10]}"


# the review UI is not carried (review is conversational); its crop test went with it
