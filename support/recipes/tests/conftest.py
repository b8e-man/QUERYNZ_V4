import pytest


@pytest.fixture(autouse=True)
def _never_the_live_servings(tmp_path, monkeypatch):
    """A test's servings go to its own folder, never <live>/recipes/servings.jsonl."""
    from support.recipes import serving
    monkeypatch.setattr(serving, "LEDGER", str(tmp_path / "servings.jsonl"))
    serving._RECORDED.clear()
