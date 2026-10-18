"""THE TRIAL'S ADDITIONS TO THE SCHEDULER'S CATALOGUE, checked here, applied
by the integrator. The trial session's fence is support/trials,
support/profiles and docs/trials; the model profiles and the job catalogue
live in support/scheduler, so the trial keeps its additions beside its own
code (`scheduler/profiles-additions.toml`, `scheduler/jobs-additions.toml`),
proves they pass the registry's own checks against the shipped catalogue,
and hands the integrator a patch.

    python -m support.trials.catalogue check     the merged catalogue passes `registry.problems`; readers and profiles agree
    python -m support.trials.catalogue patch     a unified diff for `git apply` in the main checkout
    catalogue.merged()                           (jobs_path, profiles_path) of the merged files, in a temp folder
"""
from __future__ import annotations

import difflib
import os
import sys
import tempfile

from support.scheduler import registry as reg
from support.trials import readers

HERE = os.path.dirname(os.path.abspath(__file__))
ADD_PROFILES = os.path.join(HERE, "scheduler", "profiles-additions.toml")
ADD_JOBS = os.path.join(HERE, "scheduler", "jobs-additions.toml")
REPO = os.path.dirname(os.path.dirname(HERE))
SHIPPED_PROFILES = os.path.join(REPO, "support", "scheduler", "profiles.toml")
SHIPPED_JOBS = os.path.join(REPO, "support", "scheduler", "jobs.toml")


def _read(p: str) -> str:
    with open(p, encoding="utf-8") as f:
        return f.read()


def merged_text(shipped: str, additions: str) -> str:
    base = _read(shipped).rstrip("\n") + "\n"
    add = _read(additions)
    if add.strip() in base:
        return base
    return base + "\n" + add


def merged(tmp: str = None) -> tuple[str, str]:
    tmp = tmp or tempfile.mkdtemp(prefix="qv4-trial-catalogue-")
    jp, pp = os.path.join(tmp, "jobs.toml"), os.path.join(tmp, "profiles.toml")
    with open(jp, "w", encoding="utf-8") as f:
        f.write(merged_text(SHIPPED_JOBS, ADD_JOBS))
    with open(pp, "w", encoding="utf-8") as f:
        f.write(merged_text(SHIPPED_PROFILES, ADD_PROFILES))
    return jp, pp


def problems() -> list[str]:
    """The registry's own problems on the merged catalogue, plus the trial's:
    every reader's profile exists and names the reader's weights and model."""
    import pathlib
    jp, pp = merged()
    out = list(reg.problems(pathlib.Path(jp), pathlib.Path(pp)))
    profs = reg.profiles(pathlib.Path(pp))
    jobs = reg.load(pathlib.Path(jp))
    for r in readers.READERS.values():
        p = profs.get(r.profile)
        if p is None:
            out.append(f"reader {r.name}: profile {r.profile} is not in the merged profiles")
            continue
        if p.model != r.model:
            out.append(f"reader {r.name}: profile {r.profile} serves {p.model!r}, the reader demands {r.model!r}")
        if tuple(p.weight_paths()) != tuple(r.weights):
            out.append(f"reader {r.name}: profile {r.profile} weights differ from the reader's")
        if not any(j.profile == r.profile and j.command[-1] == "piece" for j in jobs.values()):
            out.append(f"reader {r.name}: no qv4-trial-read job names profile {r.profile}")
    for j in jobs.values():
        if j.name.startswith("qv4-trial-") and not j.pieces:
            out.append(f"{j.name}: a trial job is cut into pieces")
    return out


def patch() -> str:
    out = []
    for shipped, add, rel in ((SHIPPED_JOBS, ADD_JOBS, "support/scheduler/jobs.toml"),
                              (SHIPPED_PROFILES, ADD_PROFILES, "support/scheduler/profiles.toml")):
        a = _read(shipped).splitlines(keepends=True)
        b = merged_text(shipped, add).splitlines(keepends=True)
        out += list(difflib.unified_diff(a, b, fromfile="a/" + rel, tofile="b/" + rel))
    return "".join(out)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "check"
    if cmd == "check":
        probs = problems()
        print("\n".join(probs) if probs else "catalogue: the merged catalogue passes; every reader has its profile and job")
        import pathlib
        jp, pp = merged()
        for w in reg.warnings(pathlib.Path(jp), pathlib.Path(pp)):
            if "trial" in w:
                print("  warning:", w)
        return 1 if probs else 0
    if cmd == "patch":
        sys.stdout.write(patch())
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
