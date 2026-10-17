### Databases and jobs

- **Every job's database address names the floating primary, never a box.** Old register code silently defaulted to the local machine, which on node2 is the read-only standby.
- **A wipe and reload inside one transaction never shows a reader zero rows.** With each statement committed separately, it does.
- **Database connections run out.** An old fleet took 97 of 100. Reserve some for serving and refuse to start beyond the rest.
- **Exit codes mean something:** 0 clean, 3 wrote with counted problems, 1 nothing written. A job once reported success daily because its script ended on a print statement.
- **A job's deadline must be longer than its work and shorter than its interval.** One job was killed 55 times in a week.
- **A deliberate stop must not raise the failure alarm,** and a dependent job waits for its server's health check.
- **The model server hangs for about 45 seconds after a stop signal.** Stop it with a 20-second limit and then a hard kill.
- **A memory limit above what the box has free is not a control,** and a killed run under-reports its peak.
- **Swap fullness says nothing about memory health.** Read the kernel's memory-pressure figures.
- **Before moving a folder, check the repository, the job files and the settings for anything that names it.** One move caused an unclean reboot and a missed backup.
- **Job changes are installed on both boxes and parity is checked.** node1 once ran pre-incident settings six days after the fix was written.
- **The standby once started at boot without streaming and piled up 2.7 TiB of change log.** Change-log volume fell from 244 GB a day to about 3.4 GB after tuning; read it as a daily series, not an average.
- **A refused privilege request was once read as "folder absent",** so a clean-up reported success for weeks while doing nothing.
- **An options string inside a connection string silently discards the environment's settings,** time limits included.
- **One transient error failed a whole 25 GB upload.** Retry each part with a pause.

