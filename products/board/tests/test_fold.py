"""The board's copy of keys/' readings (fold.py) is keys/' own source,
piece for piece: products may not import keys/ (imports run one way), so
the copy is held equal here by reading both files, never by importing."""
import ast
import os

from products.board import fold

REPO = os.path.join(os.path.dirname(__file__), "..", "..", "..")


def pieces(path: str) -> dict:
    src = open(path, encoding="utf-8").read()
    out = {}
    for n in ast.parse(src).body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            name = n.name
        elif isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            name = n.targets[0].id
        else:
            continue
        seg = ast.get_source_segment(src, n)
        decorators = [ast.get_source_segment(src, d) for d in getattr(n, "decorator_list", [])]
        out[name] = "\n".join("@" + d for d in decorators) + ("\n" if decorators else "") + seg
    return out


def test_every_piece_of_the_copy_is_the_keys_source():
    mine = pieces(fold.__file__)
    theirs = {**pieces(os.path.join(REPO, "keys", "names.py")), **pieces(os.path.join(REPO, "keys", "addresses.py"))}
    assert set(mine) >= {"HONORIFICS", "person_name", "ORG_WORDS", "address_key", "is_po_box", "fold_diacritics"}
    for name, src in mine.items():
        assert name in theirs, f"fold.{name} is not in keys/"
        assert src == theirs[name], f"fold.{name} differs from keys/: copy it again"


def test_the_copy_reads_as_keys_reads():
    n = fold.person_name("Rt Hon Mills, Phillip")
    assert (n.given, n.family, n.inverted) == ("Phillip", "Mills", True)
    assert fold.address_key("Level 4, 253 Queen Street, Auckland, New Zealand") == fold.address_key("level 4 253 queen st auckland")
