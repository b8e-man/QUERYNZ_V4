"""The job's contract (plan 1.9; docs/contracts/job.md). Step 2's
scheduler places jobs by it.

Every job declares what it needs, and nothing runs undeclared:

  needs            'model-profile' with the profile's name, or 'processor'
  memory_gb        memory per parallel worker, measured, never computed
  deadline_s       longer than its work and shorter than its interval; a
                   job killed at its deadline otherwise leaves its query
                   running, hence
  query_timeout_s  a statement timeout UNDER the deadline
  can_share        whether it may share a graphics card's profile slots
  prefers_memory   optionally "prefers the most memory"
  interval_s       how often it runs (0 for on demand)
  concurrency      parallel workers

A job also has, from the machinery: a record of each run, an alarm when it
fails, and the same job file installed on both boxes by one installer.
`validate` returns the problems as plain lines.
"""
from dataclasses import dataclass

NEEDS = ("model-profile", "processor")


@dataclass(frozen=True)
class JobNeeds:
    name: str                   # the unit name, with its qv4- prefix
    needs: str                  # one of NEEDS
    memory_gb: float
    deadline_s: int
    query_timeout_s: int
    interval_s: int
    model_profile: str = ""     # when needs == 'model-profile'
    can_share: bool = False
    prefers_memory: bool = False
    concurrency: int = 1


def validate(j: JobNeeds) -> list:
    out = []
    if not j.name.startswith("qv4-"):
        out.append("a job's unit name carries the qv4- prefix (hard limit 23)")
    if j.needs not in NEEDS:
        out.append(f"needs must be one of {NEEDS}")
    if j.needs == "model-profile" and not j.model_profile:
        out.append("a job that needs a model names its model profile")
    if j.needs == "processor" and j.model_profile:
        out.append("a processor job names no model profile")
    if j.memory_gb <= 0:
        out.append("memory_gb is measured and positive")
    if j.deadline_s <= 0:
        out.append("a deadline is positive")
    if j.interval_s and j.deadline_s >= j.interval_s:
        out.append("the deadline must be shorter than the interval")
    if j.query_timeout_s <= 0 or j.query_timeout_s >= j.deadline_s:
        out.append("the query time limit sits under the deadline")
    if j.concurrency < 1:
        out.append("concurrency from 1")
    return out
