"""Imports run one way (plan: "How the code is laid out"), held by this test.

  keys/        may import nothing but the standard library
  support/     keys
  registers/   keys, support — and never another lane
  links/       keys, support
  products/    support
  checks/      support

A module's own tests (a tests/ folder inside it) may also import the module
they test. The root tests/ folder is exempt: it tests everything. A second
half of the rule — no module queries the inside of another — is held by
test_no_query_crosses_a_lane once the schemas exist (step 1.8); it starts
with the only schema named so far, `pub`, which anyone may read."""
import ast
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTS = ("keys", "support", "registers", "links", "products", "checks")
MAY_IMPORT = {
    "keys": set(),
    "support": {"keys"},
    "registers": {"keys", "support"},
    "links": {"keys", "support"},
    "products": {"support"},
    "checks": {"support"},
}
STDLIB = set(sys.stdlib_module_names)


def py_files():
    for root in ROOTS:
        base = os.path.join(REPO, root)
        for dirpath, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".venv")]
            for f in files:
                if f.endswith(".py"):
                    yield os.path.join(dirpath, f)


def module_of(path: str):
    """(root, owner) for a file: owner is the lane / product / support piece —
    `registers/gazette/lane.py` → ('registers', 'registers.gazette')."""
    rel = os.path.relpath(path, REPO).split(os.sep)
    root = rel[0]
    if root in ("registers", "products", "support") and len(rel) > 2:
        return root, f"{root}.{rel[1]}"
    return root, root


def imports_of(path: str):
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name
        elif isinstance(node, ast.ImportFrom):
            if node.level:            # relative: stays inside its own package
                continue
            yield node.module or ""


def violations():
    out = []
    for path in py_files():
        root, owner = module_of(path)
        in_tests = os.sep + "tests" + os.sep in path or os.path.basename(path).startswith("test_")
        for name in imports_of(path):
            top = name.split(".")[0]
            if top in STDLIB or top not in ROOTS:
                continue   # the standard library and third-party packages are not modules of ours
            if top == root:
                # inside the same root: a lane may import only itself, and so
                # may a product shape. Pieces of support are shared machinery
                # and may use each other (the off-site copy uses db and jobrun).
                if root in ("registers", "products"):
                    target = ".".join(name.split(".")[:2])
                    if target != owner and not (in_tests and target == owner):
                        out.append(f"{os.path.relpath(path, REPO)} imports {name}: {owner} may not reach into {target}")
                continue
            if top not in MAY_IMPORT[root]:
                out.append(f"{os.path.relpath(path, REPO)} imports {name}: {root} may import only {sorted(MAY_IMPORT[root]) or 'the standard library'}")
    return out


def test_imports_run_one_way():
    bad = violations()
    assert not bad, "\n".join(bad)


# ── the query half: owner schema → module. Filled in step 1.8 from support.db. ──
import re  # noqa: E402

sys.path.insert(0, REPO)
import support.db as _db  # noqa: E402


def schema_owners() -> dict:
    """Each schema and the one module that may query inside it. None: anyone
    may read (pub). A lane owns its schema and its private twin; links owns
    both of its; a product shape owns its own; the document store and the
    seal are support's."""
    own = {"pub": None, "links": "links", "links_private": "links", "docs": "support.docstore", "sealed": "support.seal",
           "scheduler": "support.scheduler",
           "mcpsource": "support.mcpsource"}   # ruling 96: the ingest MCP's cursors, arrivals and stamps
    for lane in _db.LANES:
        own[lane] = own[lane + _db.PRIVATE_SUFFIX] = f"registers.{lane}"
    for p in _db.PRODUCTS:
        own[p] = f"products.{p}"
    return own


SCHEMA_OWNER = schema_owners()
SQL_WORD = re.compile(r"\b(select|from|join|insert|update|delete|truncate|create|alter)\b", re.I)
SQL_SHAPE = r"\b(from|join|into|update|table|truncate|only)\s+{schema}\.[a-z_][a-z0-9_]*"


def test_no_query_crosses_a_lane():
    """A string that looks like SQL and names `<schema>.<table>` right after
    FROM, JOIN, INTO, UPDATE, TABLE or TRUNCATE may appear only in the module
    that owns the schema (or anywhere, for pub)."""
    bad = []
    for path in py_files():
        root, owner = module_of(path)
        tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and SQL_WORD.search(node.value):
                for schema, who in SCHEMA_OWNER.items():
                    if who and who != owner and re.search(SQL_SHAPE.format(schema=schema), node.value, re.I):
                        bad.append(f"{os.path.relpath(path, REPO)} queries {schema}.* which belongs to {who}")
    assert not bad, "\n".join(bad)


def test_every_schema_has_an_owner():
    for s in _db.schemas():
        assert s in SCHEMA_OWNER, s


@pytest.mark.parametrize("sample,expect", [
    ("keys/x.py", ("keys", "keys")),
    ("registers/gazette/lane.py", ("registers", "registers.gazette")),
    ("support/scheduler/queue.py", ("support", "support.scheduler")),
    ("links/rules.py", ("links", "links")),
])
def test_module_of(sample, expect):
    assert module_of(os.path.join(REPO, sample)) == expect
