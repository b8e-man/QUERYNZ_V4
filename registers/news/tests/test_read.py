import contextlib
import json

from support import reader as rd
from registers.news import gates as G, read as R

ENTS = {"e1": {"name": "Richard Allen", "kind": "person", "forms": ["Richard Allen", "Allen"]},
        "e2": {"name": "Fonterra", "kind": "organisation", "forms": ["Fonterra"]},
        "e3": {"name": "Police", "kind": "organisation", "forms": ["Police"]}}
TEXT = ("Fonterra chief executive Richard Allen said they did not comment on market speculation. "
        "One person has died following a crash last night in Westmere. "
        "The report says the river is in poor health and getting worse every year.")


def test_a_quote_is_kept_only_with_its_speaker_named_beside_it_and_a_document_is_a_citation():
    near = {"text": "they did not comment on market speculation", "speaker": "e1", "channel": "interview"}
    assert G.quote(near, ENTS, TEXT)["kept"]
    far = dict(near, speaker="e3")
    assert G.quote(far, ENTS, TEXT)["rule"].startswith("the speaker is not named")
    doc = {"text": "the river is in poor health", "speaker": "e2", "channel": "document"}
    v = G.quote(doc, ENTS, TEXT)
    assert not v["kept"] and v["citation"]
    assert not G.quote(dict(near, speaker=None), ENTS, TEXT)["kept"]
    assert not G.quote(dict(near, text="words the article never prints"), ENTS, TEXT)["kept"]


def test_a_role_needs_a_title_word_and_no_of_possessive_or_leading_descriptor():
    ok = lambda role: G.role({"role": role}, ENTS, TEXT)["kept"]
    assert ok("chief executive") and ok("housing spokesperson") and ok("Senior Constable")
    assert not ok("chairs") and not ok("legends") and not ok("Labour's") and not ok("member of")
    assert not ok("former chief executive") and not ok("outgoing chair")


def test_a_claim_needs_its_claimant_and_a_verb_of_saying_in_its_own_sentence_and_the_writers_pass():
    said = {"says": "e1", "span": "they did not comment on market speculation"}
    assert G.claim(said, ENTS, TEXT)["kept"]
    fact = {"says": "e3", "span": "One person has died following a crash last night"}
    assert G.claim(fact, ENTS, TEXT)["rule"] == "the claimant is not named in the span's sentence"
    assert G.claim(dict(fact, says="writer"), ENTS, TEXT)["kept"]


def test_a_tone_needs_four_words_of_evidence():
    assert not G.tone({"evidence": "acclaimed director"}, ENTS, TEXT)["kept"]
    assert G.tone({"evidence": "a dangerous bluff that will divide"}, ENTS, TEXT)["kept"]


def test_apply_marks_every_item_and_removes_none():
    got = {"entities": ENTS, "roles": [{"role": "chief executive"}, {"role": "chairs"}],
           "quotes": [], "claims": None, "sentiment": [{"evidence": "blockbuster"}]}
    counts = G.apply(got, TEXT)
    assert counts["roles"] == {"kept": 1, "dropped": 1, "citations": 0}
    assert counts["sentiment"]["dropped"] == 1 and len(got["roles"]) == 2


class FakeConn:
    def __init__(self, article):
        self.article, self.sql = article, []

    def execute(self, sql, params=()):
        self.sql.append((sql, params))
        row = self.article if "FROM news_private.articles" in sql else None
        return type("Cur", (), {"fetchone": lambda _s: row, "fetchall": lambda _s: []})()

    @contextlib.contextmanager
    def transaction(self):
        yield

    @contextlib.contextmanager
    def cursor(self):
        conn = self

        class Cur:
            def executemany(self, sql, rows):
                conn.sql.append((sql, list(rows)))
        yield Cur()


def test_a_piece_reads_once_stores_ungated_and_replays_the_store_the_second_time(tmp_path):
    store = rd.Store(str(tmp_path))
    calls = []

    def fake_read(text, url, model):
        calls.append(text)
        assert "HEADLINE: Rumour" in text
        return ({"entities": ENTS, "roles": [{"who": "e1", "role": "chief executive", "of": "e2"}],
                 "quotes": [{"text": "they did not comment on market speculation", "speaker": "e1", "channel": "interview"}],
                 "claims": [], "sentiment": []}, "qwen4exp", 1.0)

    conn = FakeConn(("Rumour", "A Writer", TEXT))
    line = R.piece("k1", conn=conn, url="u", model="qwen4exp", store=store, read=fake_read)
    assert "read" in line and "2 of 2 items kept" in line and len(calls) == 1
    key = R.key_for(R.text_sha(R.text_of("Rumour", "A Writer", TEXT)), "qwen4exp")
    stored = json.loads(store.get(key).text)
    assert "gate" not in stored["roles"][0]            # the store holds the reading ungated
    inserted = next(rows for sql, rows in conn.sql if "INSERT INTO news_private.read_items" in sql)
    assert {(k, kept) for _, k, _, _, kept, _, _ in inserted} == {("roles", True), ("quotes", True)}
    line = R.piece("k1", conn=FakeConn(("Rumour", "A Writer", TEXT)), url="u", model="qwen4exp", store=store, read=fake_read)
    assert "replayed" in line and len(calls) == 1


def test_a_piece_refuses_without_the_workers_card(monkeypatch, capsys):
    monkeypatch.delenv("QV4_MODEL_URL", raising=False)
    monkeypatch.delenv("QV4_MODEL", raising=False)
    assert R.main(["--piece", "k1"]) == 2 and "refused" in capsys.readouterr().out


def test_te_reo_and_a_paywall_stub_are_skipped_and_recorded_without_a_model_call(tmp_path):
    reo = "Ko ngā tāngata i tahae ngā uri Tangaroa. Kua tae te wā ki te whakahau i ā tātou hunga taiohi, kia kaha rātou."
    assert R.skip_reason(reo).startswith("te reo Māori")
    assert R.skip_reason(TEXT) is None
    assert R.skip_reason("Golfer Ko edges Korda in a sensational finish, Ko said the AI caddie helped. " * 5) is None
    assert R.skip_reason(TEXT + " Already a subscriber? Sign in to continue reading") == "ends on a paywall prompt"
    conn = FakeConn(("Rongo", "", reo))
    line = R.piece("k2", conn=conn, url="u", model="qwen4exp", store=rd.Store(str(tmp_path)),
                   read=lambda *a: (_ for _ in ()).throw(AssertionError("no model call")))
    assert "skipped, te reo" in line
    done = next(p for sql, p in conn.sql if "INSERT INTO news_private.read_done" in sql)
    assert done[6] == "skipped" and "te reo" in done[8]
