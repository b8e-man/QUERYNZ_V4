The NZBN interface's role `uniqueIdentifier` is not unique within one answer: two different general partners came back under one identifier, so a role's key adds its kind and name.
area: registers/limited_partnerships, registers/companies monitor, registers/societies, any NZBN entity answer
paid-for-by: 2026-10-21, sanctions-1, step 5.3

Partnership 9429043218851 (answer d33e92fc…, 21 October 2026) lists two Active roles of type Partner with the same
`uniqueIdentifier`, two different bodies (one with an NZBN, one without). A key of identifier alone made the load
fail on a duplicate key on the first real answers; on a table without a key constraint it would have silently
dropped a general partner. Prove an interface's identifier unique on real answers before keying by it, and set aside
an exact repeat rather than letting it overwrite.
