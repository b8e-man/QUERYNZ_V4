"""healer boundaries — the EXECUTING service, and exactly that.

B4 (2026-08-22) moved mint_lane, crawler, repair and anchor_lane here
from reviewer. The contract they carried there (the 2026-08-14 healing
ruling) is now this package's contract:

- every entity/claim mutation goes through a claim_graph GATE
  (remediate / merge / the B4 split) — reversible, ledgered with a rule
  name; raw SQL touches only the lanes' own lifecycle tables and the
  claim-tier heal surface (claim_heals + the claims UPDATE in heal.py)
- nothing here ever DELETEs an entity or a claim
- no network of its own: the LLM client is reviewer.model (loopback
  only); the crossings into reviewer are named and closed
- never imports the orchestrator, the extractor, the serving layer, or
  research's web tools directly: the tier-3 re-read is
  research.crawler_judge (graph reads only) and the B4b merge refuter
  is research.merge_refuter (the ONE place web lookups reach a heal,
  refutation-only, robots-absolutist by webtools)
Same static write-grep discipline as registers/tests/test_catalog.py."""
import pathlib
import re

PKG = pathlib.Path(__file__).resolve().parents[1] / "healer"
FILES = {p.name: p.read_text() for p in PKG.glob("*.py")}
ALL = "\n".join(FILES.values())

LIFECYCLE = {"mint_review", "mint_lane_state", "anchor_review", "merge_refutations",
             "entity_renames", "entity_quarantine", "claim_object_detachments",
             "mint_review_status_idx", "entities_created_idx", "anchor_review_status_idx",
             # the re-read lane's own memory (2026-09-21): what it looked at,
             # what the document said, and what it refused to do. A lane whose
             # abstentions are not written down re-reads them every cycle and
             # never reaches the rest of the backlog.
             "reread_log"}
HEAL_SURFACE = {"v3.claim_heals", "v3.claims", "claim_heals", "claims"}
HEAL_FILES = {"heal.py", "resubject.py"}   # the claim-tier rewrite surface
WRITE = re.compile(r"(?:INSERT INTO|UPDATE|DELETE FROM|TRUNCATE|ALTER TABLE|"
                   r"CREATE TABLE IF NOT EXISTS|CREATE INDEX IF NOT EXISTS)\s+([a-zA-Z0-9_.]+)")


def test_lanes_are_here():
    for f in ("mint_lane.py", "crawler.py", "repair.py", "anchor_lane.py", "heal.py", "cli.py"):
        assert f in FILES, f"{f} missing from healer"


def test_raw_writes_confined_to_lifecycle_tables_and_the_heal_surface():
    for name, src in FILES.items():
        for stmt, target in re.findall(r"(INSERT INTO|UPDATE|DELETE FROM|TRUNCATE|ALTER TABLE|"
                                       r"CREATE TABLE IF NOT EXISTS|CREATE INDEX IF NOT EXISTS)"
                                       r"\s+([a-zA-Z0-9_.]+)", src):
            if target.lower() in ("set", "skip", "nowait", "of"):
                continue   # "UPDATE ... SET" split by an alias/newline, "FOR UPDATE SKIP LOCKED"
            if name in HEAL_FILES:
                assert target in HEAL_SURFACE, f"{name} writes {target}"
                continue
            if stmt == "ALTER TABLE" and target == "entities":
                continue   # mint_lane.ensure_schema adds quarantined_at — DDL, additive
            assert target in LIFECYCLE, f"{name}: raw write outside the lifecycle tables: {stmt} {target}"


def test_no_deletes_and_no_raw_entity_or_claim_mutation():
    assert "DELETE FROM entities" not in ALL and "DELETE FROM claims" not in ALL
    for name, src in FILES.items():
        if name in HEAL_FILES:
            continue
        assert "UPDATE entities" not in src, f"{name}: entity mutations go through claim_graph.remediate"
        assert "UPDATE claims" not in src, f"{name}: claim mutations go through claim_graph.remediate"
    assert not re.search(r"\bDELETE FROM\b", ALL), "a heal is a rewrite, never a delete"


def test_mutations_go_through_the_gates():
    for name in ("mint_lane.py", "crawler.py", "repair.py", "anchor_lane.py"):
        src = FILES[name]
        assert ("from claim_graph import remediate" in src
                or "from claim_graph.remediate import" in src
                or "from claim_graph.merge import" in src
                or "from claim_graph import merge" in src
                or "from claim_graph.split import" in src
                or "from claim_graph import split" in src), f"{name}: no gate import"


def test_no_network_of_its_own_and_named_crossings():
    for name, src in FILES.items():
        for tok in ("httpx.", "requests.", "urllib.request", "aiohttp", "nousresearch"):
            assert tok not in src, f"{name} talks to the network ({tok})"
    crossings = set(re.findall(r"from reviewer(?:\.(\w+))? import ([\w, ]+)", ALL))
    allowed = {"model", "settings", "fragments", "corroborate", "graph_handle"}
    for mod, names in crossings:
        used = {mod} if mod else {n.strip() for n in names.split(",")}
        assert used <= allowed, f"unsanctioned crossing into reviewer: {used - allowed}"
    for bad in ("import v3", "from v3", "from extractor", "from console", "from query import",
                "from research import webtools", "from research.webtools", "from registers"):
        assert bad not in ALL, f"healer imports {bad}"
    research = set(re.findall(r"from research(?:\.(\w+))? import ([\w, ]+)", ALL))
    for mod, names in research:
        used = {mod} if mod else {n.strip() for n in names.split(",")}
        # B4b: the merge refuter is the second crossing — it is where the web
        # tools live (robots absolutism in webtools, nowhere else); healer
        # still never imports webtools directly
        assert used <= {"crawler_judge", "merge_refuter"}, f"research crossing beyond the two judges: {used}"
