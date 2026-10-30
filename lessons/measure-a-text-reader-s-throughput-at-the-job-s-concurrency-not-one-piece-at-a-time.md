Measure a text reader's throughput at the job's concurrency, never from one piece's clock: 63 Beehive releases took 96 s wall four abreast (1.5 s a release) while one piece's median was 4.8 s, three times the estimate.
area: model reading, scheduler, estimates

Seen 31 October 2026 (beehive-2): the standing server (Radiance, 16 slots) serves four pieces at
nearly the speed of one, so a `pieces` job with `concurrency = 4` reads a corpus in a third of the
time the per-piece seconds suggest. Give the integrator both figures: the piece's median (what the
deadline is set from) and the wall time at the job's concurrency (what the corpus takes). Courts'
5,600 pieces at 15 a minute (30 October) were the same shape.
