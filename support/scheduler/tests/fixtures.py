"""One catalogue the policy and registry tests share: four job types on
three profiles, the shape the old fleet tests used (`doc`, `rev`, `reason`,
`emb`), carried across. `doc` and `reason` share the 50k profile (the old
"same model, same geometry" handover pair); `rev` is the same weights at
other settings (a load now, a "restart" then); `emb` is other weights."""
from __future__ import annotations

import pathlib

from support.scheduler import registry as reg

PROFILES = """
[profiles.qwen-50k]
model = "M"
weights = ["m.gguf"]
slots = 2
context = 50000
temperature = 0.0
max_tokens = 16000
memory_gb = 25.2
measured_geometry = "50000x2"

[profiles.qwen-16k]
model = "M"
weights = ["m.gguf"]
slots = 8
context = 16384
temperature = 0.6
max_tokens = 6144
memory_gb = 24.0
measured_geometry = "16384x8"

[profiles.bge]
model = "B"
weights = ["b.gguf"]
slots = 8
context = 8192
temperature = 0.0
max_tokens = 0
memory_gb = 0.7
measured_geometry = "8192x8"
embedding = true
"""

JOBS = """
version = 1
[queueing]
slice_seconds = 3600
drain_not_kill = true
min_queue_to_evict = 8
max_wait_seconds = 1800
piece_seconds = 300
due_horizon_seconds = 7200
memory_reserve_gb = 24
lease_seconds = 90
policy = "priority-ordered-round-robin"

[[reservations]]
box = "n"
card = 9
holder = "the-carve-out"
why = "test"

[jobs.doc]
needs = "model-profile"
profile = "qwen-50k"
memory_gb = 1.5
deadline_s = 900
query_timeout_s = 300
priority = 1
command = ["true"]
pieces = true
can_share = true

[jobs.rev]
needs = "model-profile"
profile = "qwen-16k"
memory_gb = 1.0
deadline_s = 300
query_timeout_s = 60
priority = 2
command = ["true"]

[jobs.reason]
needs = "model-profile"
profile = "qwen-50k"
memory_gb = 1.0
deadline_s = 400
query_timeout_s = 60
priority = 3
command = ["true"]
can_share = true

[jobs.emb]
needs = "model-profile"
profile = "bge"
memory_gb = 1.0
deadline_s = 120
query_timeout_s = 30
priority = 4
command = ["true"]

[jobs.cpu]
needs = "processor"
memory_gb = 2.0
deadline_s = 600
query_timeout_s = 60
priority = 5
command = ["true"]
"""


def write(tmp_path: pathlib.Path, jobs: str = JOBS, profiles: str = PROFILES):
    j = tmp_path / "jobs.toml"
    p = tmp_path / "profiles.toml"
    j.write_text(jobs)
    p.write_text(profiles)
    return j, p


def catalogue(tmp_path: pathlib.Path):
    """(registry, profiles, queueing) from the shared fixture; the job names
    carry no qv4- prefix on purpose, so `problems()` is tested apart."""
    j, p = write(tmp_path)
    return reg.load(j), reg.profiles(p), reg.queueing(j)
