urllib follows a 3xx by itself, so a gate that judged the URL asked must stop the transport following and hand the redirect back; a fixture `fetch` that bypasses urllib cannot prove it, test the real transport on loopback.
area: capture, fetch gate, redirects, hard limits 6 and 9, tests
paid-for-by: 2026-10-21, fix-support-fetchgate-1 (finding by grants-1)

`open_url` checked the host asked, then `urllib.request.urlopen` went wherever
the answer pointed: catalogue.data.govt.nz was answered from a host no
position named. Every test injected `fetch=`, which never touches urllib, so
none could see it. The fix is an opener whose `redirect_request` returns None
(the 3xx comes back as an HTTPError with its headers) and a test that runs a
loopback server on 127.0.0.1 redirecting to `localhost`. Same release: the
Imperva interstitial is known by its title and its X-SPA-INTERSTITIAL header,
not by "reese84", which real Imperva-protected pages load too.
