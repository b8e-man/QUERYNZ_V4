"""H.2: the finder reports places, redacts by default, compares liveness
by hash, and finds what is planted. The fixture is generated here, so no
value-shaped string is ever committed."""
import io
import os
import subprocess

from support.security import leaks, shapes

TOKEN = ("Qm7x" + "Lp3Z" * 9)[:40]           # 40 mixed characters, built at run time so no literal has a secret's shape
DSN = "postgresql://querynz:Qz9xLm2pTT7w@10.0.0.1:5432/querynz"
NTFY = "https://ntfy.sh/qnz-alerts-7f3k2"
AWS = "AK" + "IA" + "QZ7M" * 4
PLANTED = [TOKEN, "Qz9xLm2pTT7w", "qnz-alerts-7f3k2", AWS]


def _git(repo, *args):
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


def _fixture(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(str(repo), "init", "-q")
    (repo / "settings.json").write_text('{"allow": ["Bash(psql ' + DSN + ' -c select)"]}\n', encoding="utf-8")
    _git(str(repo), "add", "settings.json")
    _git(str(repo), "commit", "-q", "-m", "first")
    (repo / "settings.json").write_text('{"allow": ["Bash(psql $DSN -c select)"]}\n', encoding="utf-8")
    _git(str(repo), "commit", "-q", "-am", "cleaned: the token was " + TOKEN)
    hist = tmp_path / "bash_history"
    hist.write_text("ls\nexport CF_API_TOKEN=" + TOKEN + "\ncurl -d x " + NTFY + "\n", encoding="utf-8")
    tr = tmp_path / "projects" / "p"
    tr.mkdir(parents=True)
    (tr / "s.jsonl").write_text('{"type":"user","text":"the key is ' + AWS + ' ok"}\n{"type":"x","text":"nothing"}\n', encoding="utf-8")
    (tr / "blob.bin").write_bytes(b"\0\0" + TOKEN.encode())
    cred = tmp_path / "projects" / leaks.CRED_DIR_NAME
    cred.mkdir()
    (cred / "a.env").write_text("X=" + TOKEN + "\n", encoding="utf-8")
    return repo, hist, tr


def test_finds_each_planted_place_and_prints_no_value(tmp_path):
    repo, hist, tr = _fixture(tmp_path)
    out = io.StringIO()
    found = leaks.run([leaks.git_source(str(repo), "repo", context=True), leaks.file_source(str(hist), context=True),
                       leaks.dir_source(str(tmp_path / "projects"), context=True)], {}, out=out, context=True)
    text = out.getvalue()
    for v in PLANTED:
        assert v not in text, "a planted value reached the output"
    places = {(f.kind, f.place.split(" ", 1)[0] if f.source == "repo" else f.place) for f, _ in found}
    kinds = sorted({f.kind for f, _ in found})
    assert kinds == ["assignment", "aws-key-id", "dsn-password", "ntfy-topic", "token-40"], kinds
    assert any(f.kind == "dsn-password" and f.place.endswith("settings.json:1") for f, _ in found)
    assert any(f.kind == "token-40" and "(commit message)" in f.place for f, _ in found)
    assert any(f.kind == "assignment" and f.name == "CF_API_TOKEN" and f.place.endswith("bash_history:2") for f, _ in found)
    assert any(f.kind == "ntfy-topic" and f.place.endswith("bash_history:3") for f, _ in found)
    assert any(f.kind == "aws-key-id" and f.place.endswith("s.jsonl:1") for f, _ in found)
    assert not any("blob.bin" in f.place or leaks.CRED_DIR_NAME in f.place for f, _ in found), places
    assert "[redacted:" in text and "findings: " in text


def test_liveness_is_a_hash_comparison_with_verdicts_only(tmp_path, monkeypatch):
    repo, hist, tr = _fixture(tmp_path)
    monkeypatch.setenv("CF_API_TOKEN", TOKEN)
    monkeypatch.setenv("V3_DSN", DSN)
    monkeypatch.setenv("ALERT_NTFY_URL", NTFY)
    live = leaks.take_live(["CF_API_TOKEN", "V3_DSN", "ALERT_NTFY_URL", "MISSING"])
    assert "CF_API_TOKEN" not in os.environ and "V3_DSN" not in os.environ, "the values must be forgotten"
    assert len(live) == 3 and all(len(k) == 64 for k in live)
    out = io.StringIO()
    found = leaks.run([leaks.file_source(str(hist)), leaks.git_source(str(repo), "repo")], live, out=out)
    verdicts = {(f.kind, v) for f, v in found}
    assert ("assignment", "matches the current CF_API_TOKEN") in verdicts
    assert ("dsn-password", "matches the current V3_DSN") in verdicts
    assert ("ntfy-topic", "matches the current ALERT_NTFY_URL") in verdicts
    for v in PLANTED:
        assert v not in out.getvalue()


def test_a_differing_value_says_so(tmp_path, monkeypatch):
    repo, hist, tr = _fixture(tmp_path)
    monkeypatch.setenv("CF_API_TOKEN", ("Rt4v" + "Wk8N" * 9)[:40])
    live = leaks.take_live(["CF_API_TOKEN"])
    found = leaks.run([leaks.file_source(str(hist))], live, out=io.StringIO())
    assert all(v == "differs from every current value given" for _, v in found) and found


def test_command_line_reports_places_and_exit_code(tmp_path):
    repo, hist, tr = _fixture(tmp_path)
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(leaks.__file__))))
    report = tmp_path / "report.md"
    r = subprocess.run(["python3", "-m", "support.security.leaks", "--path", str(hist), "--report", str(report)],
                       cwd=root, capture_output=True, text=True, timeout=60)
    assert r.returncode == 1, r.stderr
    assert "bash_history:2" in r.stdout and "findings: 2" in r.stdout
    body = report.read_text(encoding="utf-8")
    assert "| assignment | CF_API_TOKEN |" in body
    for v in PLANTED:
        assert v not in r.stdout + r.stderr + body
    clean = tmp_path / "clean.txt"
    clean.write_text("nothing here\n", encoding="utf-8")
    r = subprocess.run(["python3", "-m", "support.security.leaks", "--path", str(clean)], cwd=root, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and "findings: 0" in r.stdout


def test_shapes_leave_hashes_and_git_ids_alone():
    for line in ("commit 3f2a9c1b4d5e6f708192a3b4c5d6e7f8091a2b3c", "sha256: " + "ab" * 32,
                 "postgresql://qv4_read@10.0.0.2:5432/querynz_v4", "NZBN_API_KEY=<the key>", "OFFSITE_SECRET=$(grep ...)",
                 "id: 0d49b8f4-855c-4234-b0dd-0cd4849ff418"):
        assert shapes.scan(line) == [], line
