"""The lanes' and products' own checks on the board: discovered by a main,
run as commands with a timeout, read by exit code and last lines."""
import os

from checks import module_checks as M


def fake(answers):
    return lambda name, cmd: answers[name]


def items(r):
    return {i["name"]: i for i in r["items"]}


def test_discovery_finds_every_lane_check_with_a_main_and_the_two_products(tmp_path):
    for lane, body in (("alpha", "def main(argv=None):\n    return 0\n"), ("beta", "def check():\n    pass\n"),
                       ("tenancy_tribunal", "def main():\n    pass\n")):
        d = tmp_path / "registers" / lane
        d.mkdir(parents=True)
        (d / "check.py").write_text(body)
    for prod in ("board", "published_site"):
        d = tmp_path / "products" / prod
        d.mkdir(parents=True)
        (d / "check.py").write_text("def main():\n    pass\n")
    found = M.discover(str(tmp_path))
    assert found == {"alpha": ["python", "-m", "registers.alpha.check"],
                     "board": ["python", "-m", "products.board", "check"],
                     "published_site": ["python", "-m", "products.published_site", "check"]}


def test_exit_codes_become_green_red_and_did_not_run():
    r = M.check(run=fake({"house": (0, "72 of 72 electorates join Stats NZ\nseats 123"),
                          "parties": (1, "registered 17\nshort: 1 party the page lists is not held"),
                          "companies": (3, "no answer in 600 s"),
                          "gazette": (2, "Traceback\nKeyError: 'x'")}),
                commands={"house": [], "parties": [], "companies": [], "gazette": []})
    i = items(r)
    assert not r["ok"]
    assert i["house"]["ok"] and i["house"]["detail"].startswith("72 of 72")
    assert not i["parties"]["ok"] and "short: 1 party" in i["parties"]["detail"]
    assert not i["companies"]["ok"] and "exit 3" in i["companies"]["detail"]
    assert not i["gazette"]["ok"] and "KeyError" in i["gazette"]["detail"]


def test_all_green_is_a_green_check():
    r = M.check(run=fake({"a": (0, "fine")}), commands={"a": []})
    assert r["ok"] and r["check"] == "module-checks"


def test_the_real_commands_exist_in_this_repository():
    """Every discovered command names a module file that exists; nothing is
    run here (the checks need the database and take minutes)."""
    found = M.discover()
    assert {"house", "parties", "party_returns", "disclosures", "board", "published_site"} <= set(found)
    assert not ({"tenancy_tribunal", "real_estate_authority"} & set(found))
    for name, cmd in found.items():
        mod = cmd[2]
        path = os.path.join(M.REPO, *mod.split(".")) + ".py"
        pkg = os.path.join(M.REPO, *mod.split("."), "__main__.py")
        assert os.path.exists(path) or os.path.exists(pkg), (name, cmd)


def test_a_timeout_is_a_red_item_that_says_so(tmp_path):
    script = tmp_path / "slow.py"
    script.write_text("import time\ntime.sleep(5)\n")
    rc, out = M.run_one("slow", ["python", str(script)], timeout_s=1, repo=str(tmp_path))
    assert rc == 3 and "no answer in 1 s" in out
