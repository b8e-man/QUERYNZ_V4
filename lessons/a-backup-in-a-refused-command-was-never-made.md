A hook that refuses a command refuses all of it, so a backup copy made earlier on that line was never made: check the copy exists (`cmp`, `ls`) before overwriting the file it guards.
area: sessions, hooks, scratch, working-copy

Why: construction-2 put `cp rules.py scratch/rules.new.py && git show HEAD:rules.py > rules.py && pytest … ; cp scratch/rules.new.py rules.py` on one line to run the new tests against the old rules. The scope hook refused the line for an unexpanded variable, so nothing ran. A later, separate line wrote the old rules over the edited file to re-render the checkpoint, trusting the backup from the refused line; the restore found no backup and the edits were gone. They were rebuilt only because every edit had been made by a script still in the transcript.

How to apply: make the backup its own command and confirm it before the overwrite (`cp a b && cmp a b`). Better, never overwrite the working file at all: run the old version from a scratch tree (copy the module folder there, write the old file into the copy, link what it imports), which is how the old-rules test run here worked in the end.
