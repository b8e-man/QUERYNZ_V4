# node1 was not walked for the credential inventory
kind: finding
state: open
use-case: track H
session: security
opened: 2026-10-22

H.1 asks that the inventory be walked against the file and variable names
on both boxes. Node2 was (`docs/security/inventory.md`, verdicts only).
Node1 answers on 10.0.0.10 but a login there is not on this session's
allowed list, and node1 waits on its setup card (ruling 57). Its column
in the inventory repeats what the old inventory recorded.

Owner: the session that does node1's setup, or security-2 once a login is
allowed. The walk is the same presence checks, one named variable at a
time, and the leak search's shell-history and journal sources run there
(`python -m support.security.leaks --path ~/.bash_history --journal
--journal-user`, from the checkout on node1).
