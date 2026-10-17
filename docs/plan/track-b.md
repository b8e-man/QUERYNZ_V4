### Track B: the off-site copy

**Starts** after step 1. **Model:** Opus, reviewed by the integrator.

- **Ruling 21:** the off-site copy stores changes, with a weekly full checkpoint. It has to be efficient.
- **Today** 368 GB is dumped every night and re-sent whole after any failed attempt, over a satellite link. Of that, 146 GB has no way to be rebuilt.
- **Build the new copy as new `qv4-` jobs beside the old one. The old nightly job keeps running, untouched, until a restore from the new copy has been rehearsed and passed.** Retiring the old job is then a change to the old estate, so it is Arthur's word and not before the election.
- **Sort the data by the delete rule.** What cannot be regenerated goes first and always: captured documents, decisions, corrections, document profiles, answer sets, and anything a person typed. Human review notes were once in no backup at all.
- **What can be regenerated stays out,** unless rebuilding it costs more than storing it. The vectors stay out and get a second local copy.
- **The press graph database keeps changing after the freeze,** while two old jobs, `feed-parties` and `gazette-feed`, still write to it. They are candidates to stop in step 1.4. Once they are stopped with proof, nothing writes to the press graph: take one last full copy and remove it from the nightly copy. Until then it stays in. The database itself is never dropped without Arthur's word.
- **Rehearse a restore to equality,** not to "90% of the primary", and record the time it took.

