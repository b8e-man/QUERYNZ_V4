import sys

argv = sys.argv[1:]
if argv[:1] == ["copy"]:
    from support.offsite.copy import run_job
    sys.exit(run_job(argv[1:]))
if argv[:1] == ["plan"]:
    from support.offsite.copy import plan
    sys.exit(plan())
if argv[:1] == ["restore"]:
    from support.offsite.restore import main as restore_main
    sys.exit(restore_main(argv[1:]))

from support.offsite import main  # noqa: E402 — the step 1.8 dump, until the catalogue moves to `copy`

sys.exit(main())
