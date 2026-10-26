A job that runs once is still killed (by memory, by its deadline), so it must finish on a rerun: copy rows in bulk where the target lacks them, never one call a row, and never refuse because a killed run left the target "not empty".
area: once-only jobs, adopts and exports, any bulk copy between the two databases, the document store
paid-for-by: 2026-10-27, fix-support-mcpsource-1

`qv4-mcp-adopt` re-landed 1,411,057 documents one `land()` at a time (about
21 a second, 18 hours against a 6-hour deadline), read all 1.67 M arrival
rows into memory (stopped at 1,312 MB with 1 GB declared), and refused to
start again because its first run had left the cursors behind. The bytes were
already in the one store, so the work was rows: the store's own module now
copies document and name rows for a batch of hashes in one transaction
(`copy_documents`), skipping hashes the target holds, and each table streams
COPY to COPY on two connections. 1.4 M documents in minutes at under 100 MB,
and a kill costs only the batch in flight. Also: a schema name that holds the
module's own name (`scratch_fix_support_mcpsource_1`) was mangled by two
chained `str.replace` calls in `Tables.create`; replace in one pass.
