"""Track H (H.6): no job file holds a secret. A job's credentials come only from ~/.querynz/*.env (hard limit 1), named
by the unit's EnvironmentFile or read by support.db; the catalogue, the unit files the repository ships and the qv4-
units installed on this box carry names, never values. A finding names the file, the line and the kind, never the
value (support.security.shapes)."""
import glob
import os

from support.security import shapes

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
INSTALLED = os.environ.get("QV4_UNIT_DIR") or os.path.expanduser("~/.config/systemd/user")


def job_files(root: str = ROOT, installed: str = INSTALLED) -> list:
    from support.installer import unit_sources
    out = [os.path.join(root, "support", "scheduler", "jobs.toml"), *unit_sources(root).values()]
    out += sorted(glob.glob(os.path.join(installed, "qv4-*")))
    out += sorted(glob.glob(os.path.join(installed, "qv4-*.d", "*.conf")))   # drop-ins
    return [p for p in out if os.path.isfile(p)]


def findings(paths) -> list:
    """(path, line number, kind) for every secret-shaped value; never the value."""
    out = []
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as f:
            for n, line in enumerate(f, 1):
                out.extend((p, n, h.kind) for h in shapes.scan(line))
    return out


def test_the_catalogue_and_every_qv4_unit_hold_no_secret():
    paths = job_files()
    assert any(p.endswith("jobs.toml") for p in paths) and len(paths) > 10, paths   # it looked somewhere real
    bad = findings(paths)
    assert not bad, "\n".join(f"{p}:{n}: a {k}-shaped value" for p, n, k in bad)


def test_a_planted_secret_in_a_unit_or_the_catalogue_would_fail(tmp_path):
    """Positive control: the scan fires on synthetic values in the files' own shapes, so the empty result above is a
    finding and not a silent pass."""
    unit = tmp_path / "qv4-planted.service"
    unit.write_text("[Service]\nEnvironment=QV4_DB_DSN=postgresql://qv4_owner:Qz9xLm2pTT7w@10.0.0.10:5432/querynz_v4\n",
                    encoding="utf-8")
    toml = tmp_path / "jobs.toml"
    toml.write_text('[jobs.qv4-x]\ncommand = ["python", "-m", "x", "--token", "' + ("Qm7x" + "Lp3Z" * 9)[:40] + '"]\n'
                    "env = { API_KEY = \"" + ("Ab9" * 8) + "\" }\n", encoding="utf-8")
    bad = findings([str(unit), str(toml)])
    assert {(os.path.basename(p), n) for p, n, _ in bad} >= {("qv4-planted.service", 2), ("jobs.toml", 3)}, bad
    assert all("Qz9x" not in repr(b) for b in bad)                     # a finding never carries the value
