A page is a challenge when its status, its own header or its title says so, or a body no bigger than a challenge page carries a block's mark; a word or script on a page carrying the content asked for never makes it one.
area: capture, fetch gate, recognition, failed reads, councils, InfoCouncil
paid-for-by: 2026-10-23, fix-support-fetchgate-1 (card christchurch-s-infocouncil-listing-trips-the-gate-s-challenge-check)

`looks_challenged` scanned the first 4,096 bytes of every 200 for words
such as `captcha`. Christchurch's InfoCouncil listing (795,737 bytes, 237
minutes links) carries `captcha` in a form's script near its top, so the
gate called it a challenge and the lane held the whole instance: 240 of the
old estate's minutes went unread. The earlier lesson (the results site, step
4.1) said this about a challenge script's name; a word in a form is the same
fault. The gate's rule is now: status, its own header, its title (found in
the first 64 KiB), and only then marks near the top, on a body of 64 KiB or
less. Size alone never clears a page whose title is a block's. The old
lesson that a Cloudflare shell (29 KB) outweighs a short article still
holds, so the title is read whatever the page weighs. Build the fixture from
the page's shape (its size, its links, where the word sits), not its bytes,
and check that the old code fails it before trusting the new code.
