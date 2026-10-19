# Seven stray societies tables sit in the sample's scratch schema
kind: finding
state: open
use-case: -
session: societies
opened: 2026-10-20

A full build of the societies lane was run into `scratch_societies` in
`querynz_v4_sample` with unprefixed names (`set_aside`, `files`, …), which
broke another module's sample fill (party returns writes its own
`set_aside` there). The safety hook refuses a DROP typed into a session, so
the seven were renamed, not dropped: `scratch_societies.stray_societies_*`
(six) and `scratch_societies_private.stray_societies_officer_addresses`
(empty). Scratch, regenerable: the integrator, or the next fast-tier reset
of the schema, may drop them. Lesson
`a-lane-s-tables-in-the-shared-scratch-schema-carry-its-prefix`.
