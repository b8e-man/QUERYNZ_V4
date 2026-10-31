"""A model's name enters links.rows only where its own document prints it (1 November 2026). No database."""
from links import model_check as M
from links import sightings as S
from links.rows import MODEL_VIEWS, SOURCES


def _t(text):
    return f" {S.norm(text)} "


def test_a_name_printed_whole_passes_and_case_macrons_and_spacing_do_not_matter():
    text = _t("Hon TAMA  PŌTAKA (Minister of Conservation) said Ngāti Makino Heritage Trust would")
    assert M.printed("Tama Potaka", text) and M.printed("Ngati Makino Heritage Trust", text)


def test_a_name_the_document_does_not_print_or_prints_only_in_part_fails():
    text = _t("Mr Hall gave evidence; his uncle did not. Design work was done by a company.")
    assert not M.printed("Mr Hall's uncle", text)
    assert not M.printed("design company", text)
    assert not M.printed("Hall Smith", text), "a name is whole words, not a run of letters"
    assert not M.printed("", text)


def test_every_model_view_is_a_source_the_check_reads_with_name_and_document_where_it_expects_them():
    views = {v for _, v, _ in SOURCES}
    assert MODEL_VIEWS <= views
    for _, v, sql in SOURCES:
        if v in MODEL_VIEWS:
            cols = sql.split("FROM")[0]
            assert cols.split(",")[1].strip() == "name" and cols.split(",")[7].strip() == "document", v
