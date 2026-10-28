# Two charity rows carry one NZBN, and thirty-five carry an all-zero one
kind: finding
state: open
use-case: 1
session: integrator
opened: 2026-10-28

Found by fix-links-5's live check (ruling 114's bodies table, "no NZBN names
two bodies", red from the data):

1. Thirty-five charities carry the placeholder NZBN `0000000000000`. An
   all-zero number is no number: the lane's body reading and its check
   should treat it as absent. A reading fault; the next links fix takes it.
2. CC58580 and CC61425, two dance academies registered 2020 and 2023,
   carry one real NZBN. Whether two charity rows of one NZBN are one body
   (the register re-registered the same entity) or the number is misfiled
   is a rule question for Arthur: fold them as one body, or leave two and
   abstain where a name meets both.

The check stays red on its "no NZBN names two bodies" line until both are
settled.
