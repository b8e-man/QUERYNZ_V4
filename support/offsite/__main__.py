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
print("usage: python -m support.offsite copy [--full] [--local] | plan | restore [--source local] [--keep]")
sys.exit(2)
