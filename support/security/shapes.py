"""What a secret looks like on a line, without knowing any value (track H,
hard limit 1). One shape library, shared by the leak finder
(`support/security/leaks.py`) and the inventory test (a value-shaped string
anywhere under `docs/security/` fails it).

A shape is a kind, a pattern whose group `v` is the value, and a validator
that throws out placeholders and look-alikes (a git hash is 40 hex
characters; a token is 40 mixed characters). `scan(line)` yields hits; a
hit carries the kind, the value's span and, for liveness, the value itself,
which nothing here prints: `redact(line)` is the only way text leaves.
Stdlib only."""
import re

__all__ = ["SHAPES", "Hit", "scan", "redact", "compare_key"]

# Values that mean "a value goes here", not a value.
PLACEHOLDER = re.compile(
    r"^(?:\.\.\.|…+|\*+|x+|X+|<[^>]*>|\$\{?\w+\}?|\{\{?\w+\}?\}?|%\w+%|REDACTED|redacted|changeme|change-me|example|placeholder"
    r"|p|pw|pass|passwd|password|secret|hunter2|your[-_]?\w*|none|null|todo|tbd|test|testpass|dummy|fake|sample"
    r"|\[redacted:[a-z-]+\]|\[[^\]]*\]|value|the-?value|new-?value|old-?value|unchanged|unset|empty|same)$",
    re.I)


def _not_placeholder(v: str) -> bool:
    v = v.strip("\"'`")
    return bool(v) and not PLACEHOLDER.match(v) and not v.startswith(("$", "<", "{", "…", "[", "%"))


def _mixed(v: str) -> bool:
    """Upper, lower and digit all present, and not a hexadecimal string."""
    return (any(c.isupper() for c in v) and any(c.islower() for c in v) and any(c.isdigit() for c in v)
            and not re.fullmatch(r"[0-9a-fA-F]+", v))


def _dsn_ok(m: re.Match) -> bool:
    user, pw = m.group("u"), m.group("v")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", user):
        return False   # `[:x@evil` and the like: a parser fixture, not a login
    if not _not_placeholder(pw) or len(pw) < 4:
        return False   # a password equal to the user name is a real, weak password: kept
    if user.lower() in ("user", "username", "role", "u") and pw.lower() in ("pw", "p", "pass"):
        return False
    return True


def _assign_ok(m: re.Match) -> bool:
    v = m.group("v").strip("\"'`")
    if m.group("n").upper() in ("NOPASSWD", "PASSWD") and ":" in m.group(0).split(m.group("v"))[0]:
        return False   # a sudoers tag, not a value
    if not _not_placeholder(v) or v.startswith(("$(", "`", "grep", "cut")):
        return False
    if v.lower() in ("present", "absent", "rotated", "works", "refused", "true", "false", "yes", "no"):
        return False
    if "(" in v or "[" in v or re.match(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+$", v):
        return False   # a call or an attribute path: code, not a value
    if re.match(r"^[a-z_][a-z0-9_]*$", v) and "_" in v and not any(c.isdigit() for c in v):
        return False   # a snake_case name: code, not a value
    return len(v) >= 12 or any(c.isdigit() for c in v)


def _token40_ok(m: re.Match) -> bool:
    v = m.group("v")
    if v.count("_") + v.count("-") >= 4:
        return False   # a slug (an EC file name), not a random token
    tail = m.string[m.end("v"):m.end("v") + 6]
    if tail.startswith((".pdf", ".json", ".md", ".txt", ".csv", ".html")):
        return False
    return _mixed(v)


def _topic_ok(m: re.Match) -> bool:
    v = m.group("v")
    return _not_placeholder(v) and v.lower() not in ("topic", "mytopic", "private-topic", "your-topic", "alerts", "test")


# kind, pattern (group v = the value), validator
SHAPES = [
    ("private-key", re.compile(r"(?P<v>-----BEGIN (?:OPENSSH |RSA |EC |DSA |PGP )?PRIVATE KEY(?: BLOCK)?-----)"), lambda m: True),
    ("aws-key-id", re.compile(r"(?<![A-Z0-9])(?P<v>(?:AKIA|ASIA)[0-9A-Z]{16})(?![A-Z0-9])"), lambda m: True),
    ("github-token", re.compile(r"(?<![A-Za-z0-9_])(?P<v>(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})(?![A-Za-z0-9_])"), lambda m: True),
    ("jwt", re.compile(r"(?<![A-Za-z0-9_-])(?P<v>eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,})(?![A-Za-z0-9_-])"), lambda m: True),
    ("dsn-password", re.compile(r"\b[a-z][a-z0-9+]{1,20}://(?P<u>[^\s:/@'\"\\<>]+):(?P<v>[^\s@'\"\\<>]+)@[A-Za-z0-9._-]+"), _dsn_ok),
    ("ntfy-topic", re.compile(r"https?://ntfy\.sh/(?P<v>[A-Za-z0-9_-]{6,})"), _topic_ok),
    ("apim-key", re.compile(r"Ocp-Apim-Subscription-Key[\"']?\s*[:=]\s*[\"']?(?P<v>[0-9a-fA-F]{32})\b"), lambda m: True),
    ("url-key", re.compile(r"(?<![A-Za-z0-9_])key=(?P<v>[0-9a-f]{32})(?![0-9a-f])"), lambda m: True),
    ("bearer", re.compile(r"Authorization[\"']?\s*[:=]\s*[\"']?(?:Basic|Bearer)\s+(?P<v>[A-Za-z0-9._~+/=-]{16,})"), lambda m: _not_placeholder(m.group("v"))),
    ("sk-key", re.compile(r"(?<![A-Za-z0-9_-])(?P<v>sk-[A-Za-z0-9_-]{20,})(?![A-Za-z0-9_-])"), lambda m: True),
    ("assignment", re.compile(
        r"(?<![A-Za-z0-9_])(?P<n>[A-Za-z0-9_]*(?:PASSWORD|PASSWD|PASSPHRASE|SECRET|API_KEY|APIKEY|TOKEN|ACCESS_KEY|PRIVATE_KEY|PGPASSWORD))"
        r"\s*[=:]\s*(?:\\?[\"'])?(?P<v>[^\s\"'\\,;|&<>]{8,})", re.I), _assign_ok),
    ("token-40", re.compile(r"(?<![A-Za-z0-9_/+=-])(?P<v>[A-Za-z0-9_-]{40})(?![A-Za-z0-9_/+=-])"), _token40_ok),
]
KINDS = [k for k, _, _ in SHAPES]
# A cheap gate before the shapes run: a line with none of these holds nothing.
TRIGGER = re.compile(r"-----BEGIN|AKIA|ASIA|gh[pousr]_|github_pat_|eyJ|://|ntfy\.sh|Ocp-Apim|key=|Authorization|sk-"
                     r"|(?i:password|passwd|passphrase|secret|api_key|apikey|token|access_key|private_key)"
                     r"|[A-Za-z0-9_-]{40}")


class Hit:
    __slots__ = ("kind", "name", "start", "end", "value")

    def __init__(self, kind, name, start, end, value):
        self.kind, self.name, self.start, self.end, self.value = kind, name, start, end, value

    def __repr__(self):  # never the value
        return f"Hit({self.kind}, {self.name}, {self.start}-{self.end})"


def scan(line: str):
    """Every secret-shaped value on the line, by shape, earliest first.
    The same span is reported once, by the first shape that claimed it."""
    if not TRIGGER.search(line):
        return []
    hits, taken = [], []
    for kind, pat, ok in SHAPES:
        for m in pat.finditer(line):
            if not ok(m):
                continue
            s, e = m.span("v")
            if any(s < te and e > ts for ts, te in taken):
                continue
            taken.append((s, e))
            name = m.groupdict().get("n") or ""
            if name and m.start("n") > 0 and line[m.start("n") - 1] == "\\" and name[0] in "ntr":
                name = name[1:]   # a JSON-escaped newline's letter, not part of the name
            hits.append(Hit(kind, name.upper() if name else "", s, e, m.group("v")))
    hits.sort(key=lambda h: h.start)
    return hits


def redact(line: str, hits=None) -> str:
    """The line with every secret-shaped value replaced by `[redacted:kind]`."""
    hits = scan(line) if hits is None else hits
    out, pos = [], 0
    for h in sorted(hits, key=lambda h: h.start):
        out.append(line[pos:h.start])
        out.append(f"[redacted:{h.kind}]")
        pos = h.end
    out.append(line[pos:])
    return "".join(out)


def compare_key(kind: str, value: str) -> str:
    """The part of a value that identifies it for a liveness comparison: the
    password inside a DSN, the topic of an alarm address, the token itself."""
    value = value.strip("\"'`")
    if kind == "dsn-password":
        return value
    if kind == "ntfy-topic":
        return value
    return value


def live_key(name: str, value: str) -> str:
    """What to compare a current value (from one named variable) against: a
    DSN contributes its password, an ntfy address its topic, else itself."""
    value = value.strip().strip("\"'")
    m = re.match(r"[a-z][a-z0-9+]{1,20}://[^\s:/@]+:(?P<pw>[^\s@]+)@", value)
    if m:
        return m.group("pw")
    m = re.match(r"https?://ntfy\.sh/(?P<t>[A-Za-z0-9_-]+)", value)
    if m:
        return m.group("t")
    return value
