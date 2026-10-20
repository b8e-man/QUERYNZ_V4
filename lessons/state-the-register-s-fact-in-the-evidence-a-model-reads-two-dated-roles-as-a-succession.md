When a reader is asked whether two register rows are one person, state outright in the evidence what the register says (two roles of one kind on one body at once; middle names that differ) rather than leaving two dated rows for the model to compare: shown the rows alone, the model read them as a succession and said "no reason to doubt".
area: links, the review agent, prompts and evidence, measurement
paid-for-by: 2026-10-20, review session, track C

The first smoke test of the review agent put two director rows of one name
on one company, both standing, in front of the review model with their
appointment dates. Three of four answers were "no reason to doubt": "the
different appointment dates simply reflect sequence". The register lists one
person once per company at a time, so two standing rows are two people by
the register's own practice, and the prompt said so; the model still had to
derive the overlap from two dates and did not. One field in the evidence
(`same_role_on_same_body_at_once`, computed from the filed windows) carried
that fact, and the model's catch rate on the same kind was 66 per 100 (the
screen's own rule for differing middle names took the rest). The old lesson
"screens rank, evidence convicts: don't ask the model what it cannot answer"
has a corollary: do not ask it to compute what the register already states.
