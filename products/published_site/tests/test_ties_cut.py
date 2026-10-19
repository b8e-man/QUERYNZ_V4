"""The ties the plan names are cut (4.4): nothing in this shape restarts a unit, deploys, reads the live site's
feedback, holds a token or serves on the frozen product's ports. Read from the code itself (names, imports and
string values), not from its comments or docstrings, which may say what is absent."""
import ast
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORBIDDEN_WORDS = ("subprocess", "systemctl", "cloudflare", "pi_publish", "pi_snapshot", "feedback", "token",
                   "followthemoney", "wrangler", "querynz-pi")
FROZEN_PORTS = {8300, 8301}


def sources():
    for dirpath, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in ("tests", "__pycache__")]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)


def code_words(tree):
    """Identifiers, attribute names, import names and string constants that are not docstrings."""
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                docstrings.add(id(body[0].value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, ast.Attribute):
            yield node.attr
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                yield a.name
            if isinstance(node, ast.ImportFrom) and node.module:
                yield node.module
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node.value


def test_no_module_deploys_restarts_drains_or_holds_a_token():
    for path in sources():
        tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
        for word in code_words(tree):
            low = word.lower()
            for bad in FORBIDDEN_WORDS:
                assert bad not in low, f"{os.path.relpath(path, HERE)} carries {word!r}"


def test_the_frozen_ports_appear_only_as_the_preview_s_refusal():
    for path in sources():
        tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, int) and node.value in FROZEN_PORTS:
                assert os.path.basename(path) == "preview.py", f"{os.path.relpath(path, HERE)} names port {node.value}"
        if os.path.basename(path) == "preview.py":
            found = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, int) and n.value in FROZEN_PORTS}
            assert found == FROZEN_PORTS
