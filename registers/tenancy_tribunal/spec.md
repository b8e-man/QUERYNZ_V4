owns: schema `tenancy_tribunal` (its captured decisions, by hash) and `tenancy_tribunal_private` (nothing yet)
reads: the Tenancy Tribunal's published decisions, through the fetch gate and the landing wrapper only (track E: public for three years, captured now, read in step 5)
publishes: nothing yet; capture and hold (the reading comes in step 5)
outside check: the source's own count of decisions listed for a period against the number held
jobs: a `qv4-` capture job on the scheduler's clock, once the lane's capture exists
