"""The reader's contract (plan 1.9; docs/contracts/reader.md). Step 1.10
moves the old document reader behind it.

One way to turn a document into text and rows:

- per page; the text layer first; the page reader (a model that turns a
  page image into text) only for pages the profile says have no usable
  text layer or that the surface signals mark as image pages;
- run from the document profile, by slug and version;
- every reading stamped with the reader, the model and its settings, the
  profile and version, and whether it read text or pixels;
- stored by the document's hash, so it is replayed and never re-run: the
  fast tier calls no model (ruling 50). A missing reading fails the test
  and names the document.

This module holds the record, its key and the stored-reading store the fast
tier replays from. The old estate had eleven text-extraction calls in four
shapes across nine files; this is the one shape.
"""
import hashlib
import json
import os
from dataclasses import asdict, dataclass, field

READ_FROM = ("text", "pixels")
STORE = os.environ.get("QV4_READINGS") or "/home/user/querynzv4-work/live/readings"
#: a reading made by an earlier model stands for one by the model that replaced it (Arthur, 1 November 2026: the
#: text reader moved from Flash-Next on Radiance to Qwen 3.6 35B-A3B; the Flash-Next readings already made are kept
#: and only unread documents go to Qwen 3.6). Asked for a key under the new model, the store answers with the
#: earlier model's reading when there is no new one; a new reading is always stored under its own model.
EARLIER_MODELS = {"qwen3.6-35b-a3b-q4km": ("qwen4exp",)}


def settings_hash(settings: dict) -> str:
    """A short stable hash of a model's settings (temperature, context,
    prompt version …), so two readings under different settings never
    collide."""
    return hashlib.sha256(json.dumps(settings or {}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def reading_key(document: str, page: int, model: str, settings: dict, profile: str, version: int) -> str:
    return f"{document}/p{page}/{profile}@{version}/{model}/{settings_hash(settings)}"


@dataclass(frozen=True)
class Reading:
    document: str          # sha256 of the document
    page: int              # from 1
    reader: str            # the code that made it, e.g. 'support.docread 1'
    model: str             # the served model name, or 'text-layer' for no model
    settings: dict
    profile: str
    profile_version: int
    read_from: str         # text | pixels
    text: str              # the page's text as read
    rows: list = field(default_factory=list)      # the rows the profile's tables yielded
    checks: dict = field(default_factory=dict)    # the profile's gates and their results
    made_at: str = ""

    def __post_init__(self):
        if self.read_from not in READ_FROM:
            raise ValueError(f"read_from must be one of {READ_FROM}")
        if self.page < 1:
            raise ValueError("page from 1")

    @property
    def key(self) -> str:
        return reading_key(self.document, self.page, self.model, self.settings, self.profile, self.profile_version)


class MissingReading(LookupError):
    """The fast tier found no stored reading: it names the document so the
    session can ask for a re-read job."""


class Store:
    """Stored readings, one JSON file per key, under a folder keyed by the
    document's hash. The fast tier replays from here and never calls a
    model."""

    def __init__(self, root: str = None):
        self.root = root or STORE

    def _path(self, key: str) -> str:
        doc, rest = key.split("/", 1)
        return os.path.join(self.root, doc[:2], doc, rest.replace("/", "__") + ".json")

    def put(self, reading: Reading) -> str:
        p = self._path(reading.key)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(asdict(reading), f, ensure_ascii=False)
        os.replace(tmp, p)
        return p

    def _found(self, key: str) -> str:
        """The key a reading is stored under: `key` itself, else the same key under an earlier model
        (EARLIER_MODELS), else `key` (missing)."""
        if os.path.exists(self._path(key)):
            return key
        parts = key.split("/")
        if len(parts) >= 5:
            for old in EARLIER_MODELS.get(parts[3], ()):
                alt = "/".join(parts[:3] + [old] + parts[4:])
                if os.path.exists(self._path(alt)):
                    return alt
        return key

    def get(self, key: str) -> Reading:
        p = self._path(self._found(key))
        try:
            with open(p, encoding="utf-8") as f:
                return Reading(**json.load(f))
        except OSError:
            raise MissingReading(f"no stored reading for {key}: ask for a re-read of document {key.split('/')[0]}") from None

    def has(self, key: str) -> bool:
        return os.path.exists(self._path(self._found(key)))


def replay_or_read(store: Store, key: str, read=None) -> Reading:
    """The stored reading, or, when a reader is given (never in the fast
    tier), the reading made now and stored."""
    if store.has(key):
        return store.get(key)
    if read is None:
        return store.get(key)       # raises MissingReading with the document named
    reading = read()
    if reading.key != key:
        raise ValueError(f"the reader made {reading.key}, not {key}")
    store.put(reading)
    return reading
