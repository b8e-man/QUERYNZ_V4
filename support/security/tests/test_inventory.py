"""H.1: the inventory covers every name the new estate reads, and names no
value. Fast tier; reads the repository and this box's installed qv4- units,
never the credential directory."""
import os
import subprocess
import sys

from support.security import inventory as I
from support.security import shapes

ROOT = I.ROOT


def test_inventory_exists_and_has_rows():
    have = I.inventoried()
    assert "CF_API_TOKEN" in have["names"] and "cloudflare.env" in have["files"]
    assert "QV4_OWNER_URL" in have["names"] and "v4.env" in have["files"]


def test_every_name_the_new_estate_reads_is_in_the_inventory():
    miss = I.missing()
    assert not miss["names"], {"variables read from a credential file but not in docs/security/inventory.md": miss["names"]}
    assert not miss["files"], {"credential files named by code or a qv4- unit but not in the inventory": miss["files"]}


def test_collector_sees_a_key_read_and_a_unit_env_file(tmp_path):
    """The check is only as good as its collector: a planted module and a
    planted unit must be found, or a passing test proves nothing."""
    mod = tmp_path / "support" / "thing"
    mod.mkdir(parents=True)
    (mod / "__init__.py").write_text(
        'import os\nCRED_DIR = os.environ.get("QV4_CRED_DIR")\nKEY_FILE, KEY_NAME = "planted.env", "PLANTED_API_KEY"\n'
        'def f(env):\n    return env["PLANTED_SECRET"], env.get("PLANTED_PASSPHRASE")\n', encoding="utf-8")
    units = tmp_path / "units"
    units.mkdir()
    (units / "qv4-planted.service").write_text("[Service]\nEnvironmentFile=%h/creds/planted-unit.env\n", encoding="utf-8")
    names = I.names_read_by_code(str(tmp_path))
    files = names.pop("__files__")
    assert {"PLANTED_API_KEY", "PLANTED_SECRET", "PLANTED_PASSPHRASE"} <= set(names)
    assert "planted.env" in files
    assert "planted-unit.env" in I.env_files_named_by_units(str(tmp_path), unit_dir=str(tmp_path / "none"))


def test_docs_security_names_no_value():
    assert I.values_in_docs() == []


def test_a_value_shaped_string_in_the_docs_would_fail(tmp_path):
    """Positive control: the shapes fire on a synthetic value, so the empty
    result above is a finding and not a silent pass."""
    doc = tmp_path / "inventory.md"
    doc.write_text("| secret | `postgresql://querynz:Qz9xLm2pTT7w@10.0.0.1:5432/querynz` |\n"
                   "| token | CF_API_TOKEN=" + ("Qm7x" + "Lp3Z" * 9)[:40] + " |\n"
                   "| alarm | https://ntfy.sh/qnz-alerts-7f3k2 |\n", encoding="utf-8")
    kinds = sorted(k for _, _, k in I.values_in_docs(str(tmp_path)))
    assert kinds == ["assignment", "dsn-password", "ntfy-topic"], kinds


def test_command_line_prints_verdicts_only():
    r = subprocess.run([sys.executable, "-m", "support.security.inventory"], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    for line in r.stdout.splitlines():
        assert not shapes.scan(line), "a value-shaped string in the checker's own output"
    assert "inventory covers every name the new estate reads: yes" in r.stdout
    assert "docs/security names no value: yes" in r.stdout
