Through a wall like Incapsula, reload only a 200 that is the wall's own shell (tiny, its script and nothing else); a 403 or its incident page is a refusal, never reloaded, and one refusal stops the run for the whole host, not just the path.
area: capture, headed browser, Incapsula, failed reads, hard limit 6, beehive.govt.nz
paid-for-by: 2026-10-21, diaries-1, step 6.2 template 4(a)

The first probe of www.beehive.govt.nz through a headed Chromium read the
home page cleanly (79,770 characters, no reload). Its next page,
`/advanced_search`, answered 403 with the wall's incident page, which also
carries `_Incapsula_Resource` and is under 5,000 bytes, so a "tiny page with
the wall's script means the shell, reload once" rule treated a refusal as a
shell and asked for it again. A minister's page a minute later, in a fresh
run, was refused the same way: the host had stopped serving this client.
Two lessons: test the status before the shape (`browser.reload_allowed`
needs a 200), and know the refusal page by its own words ("Incapsula
incident ID", "Request unsuccessful"), not by the script every Beehive page
carries. Search pages are where a site's wall is strictest; reach documents
by the pages that link them.
