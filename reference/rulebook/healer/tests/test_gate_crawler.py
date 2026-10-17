"""Crawler gate: deterministic heals act immediately and reversibly;
LLM findings queue under crawler-* patterns, are judged by the RIGHT
prompt, and only retype executes — observations never mutate."""
import json
import os

import pytest

from testkit import fresh_graph, graph, seed_entity  # noqa: F401

from healer import crawler, mint_lane
from reviewer import model


@pytest.fixture(autouse=True)
def _finder_state_is_throwaway(monkeypatch, tmp_path):
    """The crawler's finders write telemetry that T7.50 reads from var/audits.

    Without this, a test counting rows in a THROWAWAY SCHEMA writes those
    counts into the real state file, and the next board reads a drain that has
    "stalled" at five entities. Found 2026-09-19, the hour the telemetry
    shipped, by opening the file the test had just written — a test that writes
    into production state is the shape this repo has paid for before."""
    monkeypatch.setattr(crawler, "FINDER_STATE",
                        str(tmp_path / ("finders" + "." + "json")))


def _seed_claim(g, subj_id, obj_id, predicate):
    return g.execute("""
        INSERT INTO claims (class, predicate, subject_entity_id, object_entity_id,
                            evidence_text, document_id, extraction_method,
                            extractor_version)
        VALUES ('ROLE', %s, %s, %s, 'evidence.', gen_random_uuid(), 'test', 't1')
        RETURNING id""", (predicate, subj_id, obj_id)).fetchone()["id"]


def test_exec_role_place_detaches_and_audits(graph):
    mint_lane.ensure_schema(graph)
    p = seed_entity(graph, "Lloyd Budd", "person")
    place = seed_entity(graph, "Auckland", "place")
    cid = _seed_claim(graph, p, place, "is chief executive of")
    mayor = _seed_claim(graph, p, place, "is mayor of")   # civic — untouched
    graph.commit()
    n = crawler.heal_exec_role_places(graph)
    assert n == 1
    c = graph.execute("SELECT object_entity_id, object_text FROM claims WHERE id=%s",
                      (cid,)).fetchone()
    assert c["object_entity_id"] is None
    assert c["object_text"] == "Auckland", "the evidence survives as text"
    m = graph.execute("SELECT object_entity_id FROM claims WHERE id=%s",
                      (mayor,)).fetchone()
    assert m["object_entity_id"] == place, "mayor of a place is a real role"
    a = graph.execute("SELECT old_object_entity_id, reason FROM claim_object_detachments "
                      "WHERE claim_id=%s", (cid,)).fetchone()
    assert a["old_object_entity_id"] == place and "R-G2" in a["reason"]
    # idempotent: a second run finds nothing
    assert crawler.heal_exec_role_places(graph) == 0


def test_orphans_quarantined_reversibly(graph):
    mint_lane.ensure_schema(graph)
    orphan = seed_entity(graph, "kaimoana debris", "organisation")
    graph.commit()
    out = crawler.quarantine_orphans(graph)
    assert out["quarantined"] >= 1
    e = graph.execute("SELECT quarantined_at FROM entities WHERE id=%s",
                      (orphan,)).fetchone()
    assert e["quarantined_at"] is not None


def test_the_run_reports_what_is_LEFT_not_only_what_it_did(graph, monkeypatch):
    """Queue 8, 2026-09-19. The finder is capped, so it logged "orphans
    quarantined 500" — exactly FINDER_CAP — on 34 consecutive runs across a
    week, and that number reads the same whether 501 rows remain or five
    million. Progress, stall and disaster were indistinguishable from outside.

    `more` is the fix and it costs one row: fetch cap+1 and see if the tail is
    there."""
    mint_lane.ensure_schema(graph)
    monkeypatch.setattr(crawler, "FINDER_CAP", 2)
    for i in range(5):
        seed_entity(graph, f"debris {i}", "organisation")
    graph.commit()

    first = crawler.quarantine_orphans(graph)
    assert first["quarantined"] == 2, "the cap must still be honoured"
    assert first["more"] is True, (
        "five orphans, a cap of two: the run has to say a tail remains, or the "
        "log is a ceiling being read as a count")
    assert first["total_quarantined"] >= 2

    crawler.quarantine_orphans(graph)          # 2 more
    last = crawler.quarantine_orphans(graph)   # the 5th, and the end
    assert last["more"] is False, (
        "the run that drains the queue must say so — that is the transition "
        "nobody could see for a week")
    assert last["total_quarantined"] > first["total_quarantined"], \
        "the total is what makes progress provable from the log alone"


def _mock_type_judge(monkeypatch, verdict, confidence=0.95):
    def fake(system, user, timeout=300.0, schema=None):
        assert schema in (crawler.TYPE_SCHEMA, crawler.MULTI_SCHEMA)
        return {"verdict": verdict, "confidence": confidence,
                "reasoning": "type sanity."}
    monkeypatch.setattr(model, "judge", fake)


def test_acronym_org_retypes_at_band(graph, tmp_path, monkeypatch):
    mint_lane.ensure_schema(graph)
    eid = seed_entity(graph, "OCR", "organisation")
    graph.commit()
    monkeypatch.setattr(mint_lane, "VERDICTS_PATH",
                        str(tmp_path / "v.jsonl"))
    monkeypatch.setattr(crawler, "VERDICTS_PATH",
                        str(tmp_path / "v.jsonl"))
    assert crawler.find_acronym_orgs(graph) == 1
    _mock_type_judge(monkeypatch, "concept", 0.95)
    assert crawler.judge(graph) == 1
    stats = crawler.execute(graph)
    assert stats["retyped"] == 1
    e = graph.execute("SELECT type FROM entities WHERE id=%s", (eid,)).fetchone()
    assert e["type"] == "concept"
    ov = graph.execute("SELECT type FROM entity_type_overrides WHERE norm_form='ocr'"
                       ).fetchone()
    assert ov and ov["type"] == "concept", "future extractions bind correctly"


def test_multiplicity_is_observation_only(graph, tmp_path, monkeypatch):
    mint_lane.ensure_schema(graph)
    a = seed_entity(graph, "Moana Pasifika", "organisation")
    b = seed_entity(graph, "Moana Pasifika", "person")
    for eid in (a, b):
        for i in range(12):
            graph.execute("""
                INSERT INTO mentions (article_id, entity_id, salience, n_mentions, first_char)
                VALUES (gen_random_uuid(), %s, 'passing', 1, 0)""", (eid,))
    graph.commit()
    monkeypatch.setattr(crawler, "VERDICTS_PATH", str(tmp_path / "v.jsonl"))
    assert crawler.find_type_multiplicity(graph) == 1
    _mock_type_judge(monkeypatch, "distinct-entities-ok", 0.9)
    crawler.judge(graph)
    stats = crawler.execute(graph)
    assert stats["observed"] == 1 and stats["retyped"] == 0
    ta = graph.execute("SELECT type FROM entities WHERE id=%s", (a,)).fetchone()
    assert ta["type"] == "organisation", "observation tier never mutates"


def test_fragment_judge_never_claims_crawler_rows(graph, monkeypatch):
    mint_lane.ensure_schema(graph)
    eid = seed_entity(graph, "BYO", "organisation")
    graph.commit()
    graph.execute("""
        INSERT INTO mint_review (entity_id, name, type, pattern)
        VALUES (%s, 'BYO', 'organisation', 'crawler-acronym-org')""", (eid,))
    graph.commit()

    def explode(*a, **k):
        raise AssertionError("fragment judge must not touch crawler rows")
    monkeypatch.setattr(mint_lane.fragments, "judge_name", explode)
    assert mint_lane.judge(graph) == 0


@pytest.mark.skipif(not os.environ.get("V3_REGISTER_DSN"),
                    reason="the post-nominal fold consults the register (R-G5): with no "
                           "V3_REGISTER_DSN the register tiers ABSTAIN by design and the fold "
                           "correctly does nothing — a test that cannot decide must skip, not "
                           "read as a defect (queue 8, 2026-09-18)")
def test_post_nominal_fold_merges_into_base(graph):
    mint_lane.ensure_schema(graph)
    # a name the real register cannot hold: register count 0 -> tier-1
    # uniqueness suffices, no corroborator needed
    base = seed_entity(graph, "Zykandra Qelfrith", "person")
    suff = seed_entity(graph, "Zykandra Qelfrith CNZM", "person")
    graph.commit()
    assert crawler.heal_post_nominals(graph) == 1
    b = graph.execute("SELECT name FROM entities WHERE id=%s", (base,)).fetchone()
    assert b["name"] == "Zykandra Qelfrith", "base node survives as canonical"
    # second run finds nothing (idempotent)
    assert crawler.heal_post_nominals(graph) == 0


def test_post_nominal_fold_abstains_on_namesakes(graph):
    """False-fold guard: two live base namesakes -> NO fold (the merge
    would pick an identity by accident)."""
    mint_lane.ensure_schema(graph)
    seed_entity(graph, "Anne Norman", "person")
    seed_entity(graph, "Anne Norman", "person")     # true namesake
    seed_entity(graph, "Anne Norman CNZM", "person")
    graph.commit()
    assert crawler.heal_post_nominals(graph) == 0, "ambiguity must abstain"


def test_fold_requires_corroborator_when_register_ambiguous(graph, monkeypatch):
    """Arthur 2026-08-14: name alone never combines register occurrences.
    Register unreachable in the test env -> strictest path: every fold
    needs the shared-article corroborator."""
    mint_lane.ensure_schema(graph)
    import psycopg
    monkeypatch.setattr(psycopg, "connect",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("no register")))
    base = seed_entity(graph, "Jane Doe", "person")
    suff = seed_entity(graph, "Jane Doe QSM", "person")
    graph.commit()
    assert crawler.heal_post_nominals(graph) == 0, "no corroborator -> abstain"
    graph.execute("""
        INSERT INTO mentions (article_id, entity_id, salience, n_mentions, first_char)
        SELECT a, e, 'passing', 1, 0 FROM (VALUES (gen_random_uuid())) v(a),
             unnest(ARRAY[%s::bigint, %s::bigint]) e""", (base, suff))
    graph.commit()
    assert crawler.heal_post_nominals(graph) == 1, "shared article corroborates"


def test_article_led_folds_renames_and_abstains(graph):
    """R-G3 heal: one base -> fold; no base -> rename (old surface kept
    as alias); two bases -> abstain; persons untouched."""
    mint_lane.ensure_schema(graph)
    base = seed_entity(graph, "Fire and Emergency New Zealand", "organisation")
    fold_me = seed_entity(graph, "a Fire and Emergency New Zealand", "organisation")
    rename_me = seed_entity(graph, "a Harbourmaster Direction", "instrument")
    seed_entity(graph, "Leadership Tribunal", "organisation")
    seed_entity(graph, "Leadership Tribunal", "organisation")   # ambiguous pair
    ambiguous = seed_entity(graph, "a Leadership Tribunal", "organisation")
    person = seed_entity(graph, "a Winston Churchill", "person")
    graph.commit()
    assert crawler.heal_article_led(graph) == 2
    assert graph.execute("SELECT count(*) FROM entity_merges WHERE merged_id=%s"
                         " AND kept_id=%s", (fold_me, base)).fetchone()["count"] == 1
    r = graph.execute("SELECT name FROM entities WHERE id=%s", (rename_me,)).fetchone()
    assert r["name"] == "Harbourmaster Direction"
    for untouched in (ambiguous, person):
        row = graph.execute("SELECT name FROM entities WHERE id=%s",
                            (untouched,)).fetchone()
        assert row["name"].startswith("a ")


def test_negation_prefix_quarantines(graph):
    mint_lane.ensure_schema(graph)
    junk = seed_entity(graph, "non-NZ Government", "organisation")
    fine = seed_entity(graph, "Nongovernmental Panel", "organisation")  # no hyphen/space
    graph.commit()
    assert crawler.heal_negation_prefix(graph) == 1
    q = graph.execute("SELECT quarantined_at FROM entities WHERE id=%s",
                      (junk,)).fetchone()
    assert q["quarantined_at"] is not None
    ok = graph.execute("SELECT quarantined_at FROM entities WHERE id=%s",
                       (fine,)).fetchone()
    assert ok["quarantined_at"] is None


def test_eponym_retype_by_trailing_noun(graph):
    """R-G6: the trailing institutional noun forbids person and names the
    type; surnames that look institutional (Park) and compound debris
    (punctuation guard) are left alone."""
    mint_lane.ensure_schema(graph)
    school = seed_entity(graph, "Edmund Hillary Collegiate", "person")
    lib = seed_entity(graph, "Edmund Hillary Library", "person")
    cup = seed_entity(graph, "Kate Shepherd Cup", "person")
    park = seed_entity(graph, "Joo-won Park", "person")       # real surname
    debris = seed_entity(graph, "Lisa P / Occupy Garnet Road", "person")
    graph.commit()
    n = crawler.heal_eponym_retype(graph)
    assert n == 3
    got = {r["id"]: r["type"] for r in graph.execute(
        "SELECT id, type FROM entities WHERE id = ANY(%s)",
        ([school, lib, cup, park, debris],)).fetchall()}
    assert got[school] == "organisation"
    assert got[lib] == "facility"
    assert got[cup] == "work"
    assert got[park] == "person"
    assert got[debris] == "person", "punctuation guard: not this heal's case"
    a = graph.execute("SELECT reason FROM entity_type_changes WHERE entity_id=%s",
                      (school,)).fetchone()
    assert a and "R-G6" in a["reason"]
    # idempotent: a second run finds nothing
    assert crawler.heal_eponym_retype(graph) == 0


def test_definite_article_fold_protects_allowlist(graph):
    """R-G7: the-doubles fold into the bare node; THE_NAMES survive;
    persons are skipped."""
    mint_lane.ensure_schema(graph)
    bare = seed_entity(graph, "High Court", "organisation")
    the = seed_entity(graph, "The High Court", "organisation")
    spinoff = seed_entity(graph, "The Spinoff", "organisation")  # allowlisted
    lonely = seed_entity(graph, "The Wairoa Working Group", "organisation")
    person = seed_entity(graph, "The Rock Johnson", "person")
    caps = seed_entity(graph, "THE PANEL", "organisation")   # case-blind strip
    graph.commit()
    n = crawler.heal_definite_article(graph)
    assert n == 3
    assert graph.execute("SELECT 1 FROM entities WHERE id=%s", (the,)).fetchone() is None
    m = graph.execute("SELECT kept_id, reason FROM entity_merges WHERE merged_name=%s",
                      ("The High Court",)).fetchone()
    assert m["kept_id"] == bare and "R-G7" in m["reason"]
    got = {r["id"]: r["name"] for r in graph.execute(
        "SELECT id, name FROM entities WHERE id = ANY(%s)",
        ([spinoff, lonely, person],)).fetchall()}
    assert got[spinoff] == "The Spinoff", "allowlist protected"
    assert got[lonely] == "Wairoa Working Group", "no base -> renamed bare"
    assert got[person] == "The Rock Johnson", "persons skipped"
    caps_row = graph.execute("SELECT name FROM entities WHERE id=%s",
                             (caps,)).fetchone()
    assert caps_row["name"] == "PANEL", "all-caps THE strips too"
    assert crawler.heal_definite_article(graph) == 0, "idempotent"


def test_caption_credit_strip_fold_and_debris(graph):
    """R-G8: caption glue comes off; the survivor folds into its bare
    twin or renames; a base too short to be a name quarantines."""
    mint_lane.ensure_schema(graph)
    bare = seed_entity(graph, "Bill English", "person")
    glued = seed_entity(graph, "Bill English Photo: Supplied", "person")
    lone = seed_entity(graph, "Aneta Cram Photo: Supplied", "person")
    stub = seed_entity(graph, "Pawarenga (Photo: Supplied", "person")
    video = seed_entity(graph, "Blockbuster Video", "organisation")  # real name
    graph.commit()
    n = crawler.heal_caption_credit(graph)
    assert n == 3
    assert graph.execute("SELECT 1 FROM entities WHERE id=%s", (glued,)).fetchone() is None
    m = graph.execute("SELECT kept_id FROM entity_merges WHERE merged_name=%s",
                      ("Bill English Photo: Supplied",)).fetchone()
    assert m["kept_id"] == bare
    got = {r["id"]: r for r in graph.execute(
        "SELECT id, name, quarantined_at FROM entities WHERE id = ANY(%s)",
        ([lone, stub, video],)).fetchall()}
    assert got[lone]["name"] == "Aneta Cram"
    assert got[stub]["quarantined_at"] is not None, "single-token person = debris"
    assert got[video]["name"] == "Blockbuster Video", "real names untouched"
    assert crawler.heal_caption_credit(graph) == 0, "idempotent"


def test_lead_junk_strip(graph):
    """R-G9: bullets/dashes/orphan quotes come off; survivor folds or
    renames; short person bases quarantine."""
    mint_lane.ensure_schema(graph)
    goff = seed_entity(graph, "Phil Goff", "person")
    dashed = seed_entity(graph, "— Phil Goff", "person")
    bullet = seed_entity(graph, "• Accenture", "organisation")
    quoted = seed_entity(graph, "'Skinny Tahi", "organisation")
    graph.commit()
    n = crawler.heal_lead_junk(graph)
    assert n == 3
    m = graph.execute("SELECT kept_id FROM entity_merges WHERE merged_name=%s",
                      ("— Phil Goff",)).fetchone()
    assert m["kept_id"] == goff
    got = {r["id"]: r["name"] for r in graph.execute(
        "SELECT id, name FROM entities WHERE id = ANY(%s)",
        ([bullet, quoted],)).fetchall()}
    assert got[bullet] == "Accenture"
    assert got[quoted] == "Skinny Tahi"
    assert crawler.heal_lead_junk(graph) == 0, "idempotent"


def test_trailing_function_word_strip(graph):
    """R-G10: mid-phrase cuts lose their dangling connectors."""
    mint_lane.ensure_schema(graph)
    cut = seed_entity(graph, "North End Health Centre and", "organisation")
    deep = seed_entity(graph, "Kissinger & The", "organisation")
    fine = seed_entity(graph, "Bank of New Zealand", "organisation")
    graph.commit()
    n = crawler.heal_trailing_function_word(graph)
    assert n == 2
    got = {r["id"]: r["name"] for r in graph.execute(
        "SELECT id, name FROM entities WHERE id = ANY(%s)",
        ([cut, deep, fine],)).fetchall()}
    assert got[cut] == "North End Health Centre"
    assert got[deep] == "Kissinger", "iterative: '& The' strips fully"
    assert got[fine] == "Bank of New Zealand", "mid-name 'of' untouched"
    assert crawler.heal_trailing_function_word(graph) == 0, "idempotent"


def test_orthography_twin_folds(graph):
    """Macron twin folds into the macronned node; case twin folds into
    the mixed-case node; 1-1 same-type pairs only."""
    mint_lane.ensure_schema(graph)
    mac = seed_entity(graph, "Ngāti Kōwhai Trust", "organisation")
    plain = seed_entity(graph, "Ngati Kowhai Trust", "organisation")
    mixed = seed_entity(graph, "Kerry Prendergast", "person")
    caps = seed_entity(graph, "KERRY PRENDERGAST", "person")
    graph.commit()
    n = crawler.heal_orthography_twins(graph)
    assert n == 2
    for lose, keep, label in ((plain, mac, "macron"), (caps, mixed, "case")):
        assert graph.execute("SELECT 1 FROM entities WHERE id=%s",
                             (lose,)).fetchone() is None, label
        assert graph.execute("SELECT 1 FROM entities WHERE id=%s",
                             (keep,)).fetchone() is not None, label
    assert crawler.heal_orthography_twins(graph) == 0, "idempotent"


def test_url_fragments_quarantine(graph):
    """R-G11: protocol/www names quarantine; bare domains are outlets."""
    mint_lane.ensure_schema(graph)
    junk = seed_entity(graph, "Facebook Page - https://www", "person")
    outlet = seed_entity(graph, "interest.co.nz", "organisation")
    graph.commit()
    assert crawler.heal_url_fragments(graph) == 1
    got = {r["id"]: r["quarantined_at"] for r in graph.execute(
        "SELECT id, quarantined_at FROM entities WHERE id = ANY(%s)",
        ([junk, outlet],)).fetchall()}
    assert got[junk] is not None and got[outlet] is None
    assert crawler.heal_url_fragments(graph) == 0, "idempotent"


def test_role_title_prefix_fold(graph, monkeypatch):
    """R-G12: the title comes off; fold needs a namesake-unique base
    (register-corroborated when the register is ambiguous)."""
    from reviewer import corroborate
    monkeypatch.setattr(corroborate, "register_conn", lambda: None)
    monkeypatch.setattr(corroborate, "register_namesakes", lambda reg, n: 1)
    mint_lane.ensure_schema(graph)
    bare = seed_entity(graph, "Chris Hipkins", "person")
    titled = seed_entity(graph, "Prime Minister Chris Hipkins", "person")
    lone = seed_entity(graph, "Mayor Tory Whanau", "person")
    rank = seed_entity(graph, "Major Tom Jones", "person")  # rank = real name
    graph.commit()
    n = crawler.heal_role_title_prefix(graph)
    assert n == 2
    m = graph.execute("SELECT kept_id FROM entity_merges WHERE merged_name=%s",
                      ("Prime Minister Chris Hipkins",)).fetchone()
    assert m["kept_id"] == bare
    got = {r["id"]: r["name"] for r in graph.execute(
        "SELECT id, name FROM entities WHERE id = ANY(%s)",
        ([lone, rank],)).fetchall()}
    assert got[lone] == "Tory Whanau"
    assert got[rank] == "Major Tom Jones", "bare ranks deliberately absent"
    assert crawler.heal_role_title_prefix(graph) == 0, "idempotent"


def test_ampersand_twin_fold(graph):
    """'X & Y' and 'X and Y' fold; register side keeps, else older node."""
    mint_lane.ensure_schema(graph)
    amp = seed_entity(graph, "Johnson & Johnson", "organisation")
    spelled = seed_entity(graph, "Johnson and Johnson", "organisation")
    graph.commit()
    assert crawler.heal_ampersand_twins(graph) == 1
    assert graph.execute("SELECT 1 FROM entities WHERE id=%s",
                         (amp,)).fetchone() is not None, "older node keeps"
    assert graph.execute("SELECT 1 FROM entities WHERE id=%s",
                         (spelled,)).fetchone() is None
    assert crawler.heal_ampersand_twins(graph) == 0, "idempotent"


# ── C247: the party name cut at a word boundary ─────────────────────────────

def _seed_claim_ev(g, subj_id, obj_id, predicate, evidence):
    return g.execute("""
        INSERT INTO claims (class, predicate, subject_entity_id, object_entity_id,
                            evidence_text, document_id, extraction_method,
                            extractor_version)
        VALUES ('ROLE', %s, %s, %s, %s, gen_random_uuid(), 'test', 't1')
        RETURNING id""", (predicate, subj_id, obj_id, evidence)).fetchone()["id"]


def test_party_boundary_detaches_the_country_from_a_leader_claim(graph):
    """"Winston Peters is leader of New Zealand" — 164 of these on the live
    graph, every one the same cut. The edge goes; the evidence stays."""
    mint_lane.ensure_schema(graph)
    p = seed_entity(graph, "Winston Peters", "person")
    nz = seed_entity(graph, "New Zealand", "place")
    cid = _seed_claim_ev(graph, p, nz, "is leader of",
                         "New Zealand First's leader Winston Peters said so.")
    graph.commit()
    assert crawler.heal_party_boundary(graph) == 1
    c = graph.execute("SELECT object_entity_id, object_text, evidence_text "
                      "FROM claims WHERE id=%s", (cid,)).fetchone()
    assert c["object_entity_id"] is None
    assert c["object_text"] == "New Zealand", \
        "the old reading survives as text; the party is the NEXT era's answer, not a guess here"
    assert c["evidence_text"].startswith("New Zealand First"), "the evidence was touched"
    a = graph.execute("SELECT old_object_entity_id, reason FROM claim_object_detachments "
                      "WHERE claim_id=%s", (cid,)).fetchone()
    assert a["old_object_entity_id"] == nz and "C247" in a["reason"], a


def test_a_true_claim_about_the_country_is_not_swept(graph):
    """The reverse direction, and the reason the heal stops at leader-class:
    "…New Zealand, when former prime minister Helen Clark clung to New Zealand
    First support…" is CORRECT about the country. A heal keyed on the sentence
    alone would destroy it to reach eight rows."""
    mint_lane.ensure_schema(graph)
    hc = seed_entity(graph, "Helen Clark", "person")
    nz = seed_entity(graph, "New Zealand", "place")
    cid = _seed_claim_ev(graph, hc, nz, "is former prime minister of",
                         "The situation is not without parallel in New Zealand, when "
                         "former prime minister Helen Clark clung to New Zealand First support.")
    graph.commit()
    assert crawler.heal_party_boundary(graph) == 0
    c = graph.execute("SELECT object_entity_id FROM claims WHERE id=%s", (cid,)).fetchone()
    assert c["object_entity_id"] == nz, "a true claim was detached"


def test_a_leader_claim_with_no_party_in_the_sentence_is_left_alone(graph):
    """The sentence is the evidence. Without "New Zealand First" in it there is
    nothing to say the object was cut, and abstain is the design."""
    mint_lane.ensure_schema(graph)
    p = seed_entity(graph, "Jacinda Ardern", "person")
    nz = seed_entity(graph, "New Zealand", "place")
    _seed_claim_ev(graph, p, nz, "is leader of",
                   "As leader of New Zealand she addressed the United Nations.")
    graph.commit()
    assert crawler.heal_party_boundary(graph) == 0


def test_the_heal_runs_in_the_crawler_not_only_by_hand(graph):
    """A deterministic heal that nothing calls is a heal that never runs. The
    crawler is on querynz-crawler.timer every two hours (ruling 20)."""
    import inspect
    src = inspect.getsource(crawler.run)
    assert "heal_party_boundary(g)" in src


# ── C252: an honorific plus an initial is nobody ────────────────────────────

def test_anonymised_honorifics_are_quarantined_not_deleted(graph):
    """102 of these were live, "Miss M." alone carrying 2,192 claims. They are
    the whole point of a suppression order, so they leave the graph — but
    reversibly, and the evidence stays where it is."""
    mint_lane.ensure_schema(graph)
    miss = seed_entity(graph, "Miss M.", "person")
    hon = seed_entity(graph, "Rt Hon B.", "person")
    real = seed_entity(graph, "Rt Hon Winston Peters", "person")
    named = seed_entity(graph, "Justice Williams", "person")
    graph.commit()
    n = crawler.heal_anonymised_honorifics(graph)
    assert n == 2, n
    gone = graph.execute("SELECT id FROM entities WHERE quarantined_at IS NOT NULL").fetchall()
    assert {g["id"] for g in gone} == {miss, hon}
    kept = graph.execute("SELECT count(*) AS n FROM entities WHERE id = ANY(%s) "
                         "AND quarantined_at IS NULL", ([real, named],)).fetchone()
    assert kept["n"] == 2, "a named person was quarantined"


def test_the_heal_and_the_mint_guard_cannot_disagree(graph):
    """The predicate is IMPORTED, never restated. A copy here would test the
    copy — the failure mode this estate has paid for more than once."""
    import inspect
    src = inspect.getsource(crawler.heal_anonymised_honorifics)
    assert "from reconciliation.lexicons import is_anonymised" in src
    assert "is_anonymised(r[\"name\"])" in src


def test_a_register_asserted_name_is_never_quarantined(graph):
    """A register ASSERTS a name; an article parse GUESSES one, and only a
    guess can be junk — the same safety the name-fragment rule needed."""
    mint_lane.ensure_schema(graph)
    e = seed_entity(graph, "Miss M.", "person")
    graph.execute("UPDATE entities SET register_source = 'companies' WHERE id = %s", (e,))
    graph.commit()
    assert crawler.heal_anonymised_honorifics(graph) == 0


def test_the_heal_runs_in_the_crawler(graph):
    import inspect
    assert "heal_anonymised_honorifics(g)" in inspect.getsource(crawler.run)


# ── C235: OCR debris, recovered where it can be ─────────────────────────────

def test_ocr_debris_folds_into_the_real_name_when_there_is_one(graph):
    """Two of forty in the live sample were real names wearing a stray caret.
    Recover over exclude: strip, and if the clean name already exists, this
    row is a mangled duplicate of it."""
    mint_lane.ensure_schema(graph)
    real = seed_entity(graph, "William O'Brien", "person")
    mangled = seed_entity(graph, "William O'Brien^", "person")
    graph.commit()
    out = crawler.heal_ocr_debris(graph)
    assert out["folded"] == 1 and out["quarantined"] == 0, out
    assert graph.execute("SELECT quarantined_at FROM entities WHERE id=%s",
                         (real,)).fetchone()["quarantined_at"] is None


def test_debris_with_nothing_to_recover_is_quarantined(graph):
    mint_lane.ensure_schema(graph)
    junk = seed_entity(graph, "Sheep Farm of f{f ACRES", "organisation")
    graph.commit()
    out = crawler.heal_ocr_debris(graph)
    assert out["quarantined"] == 1 and out["folded"] == 0, out
    assert graph.execute("SELECT quarantined_at FROM entities WHERE id=%s",
                         (junk,)).fetchone()["quarantined_at"] is not None


def test_the_strip_is_never_allowed_to_invent_a_name(graph):
    """"^^T^" strips to "T". Folding that into any entity called T would be
    the heal inventing an identity, so one token is refused outright."""
    mint_lane.ensure_schema(graph)
    seed_entity(graph, "T", "person")
    seed_entity(graph, "^^T^", "person")
    graph.commit()
    out = crawler.heal_ocr_debris(graph)
    assert out["folded"] == 0 and out["quarantined"] == 1, out


def test_one_surname_is_not_an_identity(graph):
    """A single token clears the letter-count floor and still names nobody in
    particular: "Smith^" beside a "Smith" entity is not evidence they are the
    same person. TWO tokens is the weakest reading that carries an identity."""
    mint_lane.ensure_schema(graph)
    seed_entity(graph, "Smith", "person")
    seed_entity(graph, "Smith^", "person")
    graph.commit()
    out = crawler.heal_ocr_debris(graph)
    assert out["folded"] == 0 and out["quarantined"] == 1, out


def test_two_possible_targets_abstain_into_quarantine(graph):
    """A rule that cannot decide leaves the row alone — here that means the
    reversible disposition, not a coin toss between two people."""
    mint_lane.ensure_schema(graph)
    seed_entity(graph, "John Smith", "person")
    graph.execute("INSERT INTO entities (name, type) VALUES ('John Smith', 'person')")
    seed_entity(graph, "John Smith^", "person")
    graph.commit()
    out = crawler.heal_ocr_debris(graph)
    assert out["folded"] == 0 and out["quarantined"] == 1, out


def test_a_register_asserted_name_is_left_alone(graph):
    mint_lane.ensure_schema(graph)
    e = seed_entity(graph, "ODD|NAME LIMITED", "organisation")
    graph.execute("UPDATE entities SET register_source='companies' WHERE id=%s", (e,))
    graph.commit()
    out = crawler.heal_ocr_debris(graph)
    assert out["folded"] == 0 and out["quarantined"] == 0, out


def test_the_run_says_what_is_left_not_only_what_it_did(graph):
    """Queue 8's lesson, applied at birth this time: 1,024,328 rows against a
    500-per-run cap is 170 days, and a log line that only ever prints the cap
    cannot tell progress from a stall."""
    mint_lane.ensure_schema(graph)
    seed_entity(graph, "junk|one", "organisation")
    seed_entity(graph, "junk|two", "organisation")
    graph.commit()
    out = crawler.heal_ocr_debris(graph)
    assert set(out) == {"folded", "quarantined", "left", "more"}
    assert out["left"] == 0, out


def test_the_heal_runs_in_the_crawler_too(graph):
    import inspect
    assert "heal_ocr_debris(g)" in inspect.getsource(crawler.run)


# ── C241: glued punctuation ─────────────────────────────────────────────────

def test_glued_prose_is_cut_and_folded_into_the_real_name(graph):
    mint_lane.ensure_schema(graph)
    real = seed_entity(graph, "Ministry of Justice", "organisation")
    glued = seed_entity(graph, "repeal.428 Ministry of Justice", "organisation")
    graph.commit()
    assert crawler.heal_glued_punctuation(graph) == 1
    assert graph.execute("SELECT quarantined_at FROM entities WHERE id=%s",
                         (real,)).fetchone()["quarantined_at"] is None


def test_a_single_token_recovery_must_fold_never_rename(graph):
    """"sidehead)Today" recovers "Today", which is a word, not a name. Where
    an entity of that name exists the fold is evidence that it IS one; where
    none does, renaming to it would trade a glued name for a bare one."""
    mint_lane.ensure_schema(graph)
    seed_entity(graph, "sidehead)Today", "organisation")
    graph.commit()
    assert crawler.heal_glued_punctuation(graph) == 0
    seed_entity(graph, "Today", "organisation")
    graph.commit()
    assert crawler.heal_glued_punctuation(graph) == 1


def test_two_names_run_together_are_left_alone(graph):
    mint_lane.ensure_schema(graph)
    e = seed_entity(graph, "Phototek)New Caledonia", "organisation")
    graph.commit()
    assert crawler.heal_glued_punctuation(graph) == 0
    row = graph.execute("SELECT name, quarantined_at FROM entities WHERE id=%s",
                        (e,)).fetchone()
    assert row["name"] == "Phototek)New Caledonia" and row["quarantined_at"] is None


def test_ocr_debris_is_left_to_its_own_heal(graph):
    """The two classes overlap and each must dispose of its own, or a row gets
    renamed by one rule and quarantined by the other on the same run."""
    mint_lane.ensure_schema(graph)
    # carries BOTH marks: the glue seam and C235's impossible glyph
    seed_entity(graph, "repeal|s.428 Ministry of Health", "organisation")
    seed_entity(graph, "Ministry of Health", "organisation")
    graph.commit()
    assert crawler.heal_glued_punctuation(graph) == 0


def test_the_glue_heal_runs_in_the_crawler(graph):
    import inspect
    assert "heal_glued_punctuation(g)" in inspect.getsource(crawler.run)
