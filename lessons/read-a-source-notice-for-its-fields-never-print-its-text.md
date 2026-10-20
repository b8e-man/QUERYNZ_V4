When a checkpoint reads a fact against its source document, extract only the fields being checked (a date, a name, a section): never print a notice's text into the session, because a Gazette prohibition notice carries the person's home address.
area: checkpoints, reading against source, Gazette, hard limit 11, subject reports
paid-for-by: 2026-10-20, banking-1 session, step 5.2 checkpoint

The banking checkpoint read three facts against the Gazette source file by
grepping a window of text around each notice number. The prohibition
notice's text names the prohibited person "Of:" their street address, and
it was printed into the session's transcript: hard limit 11 says never.
The second pass read the same file with a few lines of Python that parsed
each JSON line and printed only the notice number, its published day and
the dates the text holds, which is all the check needed. Write the
extraction so its output cannot hold more than the fields compared.
