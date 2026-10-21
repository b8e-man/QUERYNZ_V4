A leak search compares what it finds against the current value by hash, with the value handed in through one named variable, so "still live" is a verdict and no secret is ever printed, listed or kept.
area: security, track H, credentials, transcripts, shell history, hard limit 1
paid-for-by: 2026-10-22, security-1 session, H.2 (support/security/leaks.py)

Track H asks, for every place a secret has leaked, whether it is still
live. The obvious way is to read the credential file and look: forbidden.
The way that works is the standing shape, `NAME=$(grep '^NAME=' file |
cut -d= -f2-)` in front of the finder, which hashes the value's comparison
key (a DSN's password, an alarm address's topic, a token itself), forgets
the variable before any child process starts, and labels each hit
"matches the current NAME" or "differs from every current value given".
The finder's output is places and kinds; a redacted window is an option,
never the default.

Two shape lessons from the first run, each a false-positive class that
swamped the real hits until it was named: a 40-character "token" that is
a file-name slug (an EC return's name, four or more separators), and an
"assignment" whose value is code (`re.compile(`, `settings.api_key`, a
sudoers `NOPASSWD:` tag). Tune by excluding the class, not by weakening
the shape, and keep a positive control in the test so an empty result
stays a finding and not a silent pass.
