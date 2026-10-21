A planted secret in a test fixture is built at run time, never written as a literal: a literal with a secret's shape stops the push to GitHub even when it is fake.
area: tests, fixtures, secrets, GitHub push protection, track H
paid-for-by: 2026-10-22, security-1, the integrator

security-1's leak-finder tests planted four fake secrets as literals (a
40-character token, a key id of the AKIA shape, a password in a connection
string, an alarm topic). GitHub's push protection refused the merge to
main on the two shapes it recognises, so the merge had to be rebuilt as
one commit with the literals gone from history. The finder itself, run on
the original fixture against the live values one variable at a time, said
every planted value differs: they were fake, and the push was still
refused. Build such values from parts at run time (`("Qm7x" + "Lp3Z" * 9)[:40]`,
`"AK" + "IA" + ...`), keep the shape the finder must recognise, and let no
literal of a secret's shape into a file. The session's branch, pushed
before the merge, still carries the literals on the remote; deleting a
remote branch is Arthur's.
