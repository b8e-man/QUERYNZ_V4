# The gate's open_url follows a redirect to another host without asking the gate, and hands back gzip undecoded
kind: finding
state: open
use-case: -
session: windowed
opened: 2026-10-18

Found building track E's capture. Two things in `support.fetchgate.open_url`:

1. It uses `urllib.request.urlopen`, which follows a 30x to any host. The
   gate decides for the URL asked, never for the URL answered: a permitted
   host that redirects to a held host (NZME, fyi.org.nz) or to a host with no
   position would be read. `Fetched.final_url` is returned, but nothing
   checks it. Fix: an opener whose redirect handler calls `check()` on each
   new location (and refuses on a held host), with a test.
2. The Ministry of Justice's listing service answers gzip although the
   request does not ask for it; `open_url` returns the compressed bytes. The
   tenancy lane decodes it itself (`capture.decode`). Fix: decode a
   `Content-Encoding: gzip` body in the gate, so every lane lands the
   document and not its transfer encoding.

The two windowed hosts did not redirect on any page read on 18 October.

19 October (windowed session 2): both windowed lanes now stop on an answer
from another host and land nothing from it (`Run.get`, tested). That keeps
such a page out of the store but not out of the read: the gate fix above is
still the one that keeps a held host from being read at all.
