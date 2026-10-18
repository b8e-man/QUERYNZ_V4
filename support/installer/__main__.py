"""  python -m support.installer plan [--box HOST]        what installing would do on this box (and the other)
  python -m support.installer apply [--units] [--box HOST]
        model server beside the old one, venv, models check; --units also places the qv4- unit
        files and enables the timers and this box's worker (an integrator's step); --box copies
        code, models and credentials to a second box directly
  python -m support.installer check [--box HOST]       the parity report
  python -m support.installer build [--ref REF]        the model server built from source, beside the copy"""
from __future__ import annotations

import argparse
import json
import sys

from support import installer as inst
from support.scheduler import registry as reg


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m support.installer", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("plan", "apply", "check", "build"))
    ap.add_argument("--ref", help="build: the source commit or tag (default: the old checkout's HEAD)")
    ap.add_argument("--box")
    ap.add_argument("--units", action="store_true")
    ap.add_argument("--repo", default=inst.REPO, help="install from this checkout (a working copy for a rehearsal)")
    ap.add_argument("--only", nargs="*", default=(), help="units: place only these")
    a = ap.parse_args(argv)
    profiles = reg.profiles()
    if a.cmd == "build":
        rec = inst.build_model_server(ref=a.ref)
        print(json.dumps(rec, indent=1))
        return 0 if rec.get("action") == "build" else 1
    if a.cmd in ("plan", "check"):
        print(json.dumps(inst.check(profiles, repo=a.repo, box=a.box), indent=1))
        return 0
    out = {"model_server": inst.install_model_server(), "venv": inst.install_venv(), "models": inst.plan_models(profiles)}
    if a.units:
        out["units"] = inst.install_units(repo=a.repo, box=a.box, only=tuple(a.only))
    if a.box:
        out["code"] = inst.plan_code(box=a.box)
        out["models_copied"] = inst.copy_models(profiles, a.box)
        out["credentials"] = inst.copy_credentials(a.box)
    print(json.dumps(out, indent=1))
    missing = [m for m in out["models"] if not m["present"]]
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
