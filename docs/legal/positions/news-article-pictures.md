# A news article's lead picture, found on its own page (position, hard limit 9)

hosts: nzherald.co.nz, odt.co.nz, scoop.co.nz, rnz.co.nz, stuff.co.nz, kiwiblog.co.nz, thespinoff.co.nz, waateanews.com, 1news.co.nz, localmatters.co.nz, farmersweekly.co.nz, hospitalitybusiness.co.nz, greens.org.nz, act.org.nz, buildingtoday.co.nz, tpplus.co.nz, national.org.nz, businessdesk.co.nz, wbn.co.nz, valleyprofile.co.nz, sciencemediacentre.co.nz, hrc.govt.nz, kanivatonga.co.nz, newsroom.co.nz, nztrucking.co.nz, sunlive.co.nz, times.co.nz, interest.co.nz, regulation.govt.nz, labour.org.nz, guardianonline.co.nz, baybuzz.co.nz, opportunity.org.nz, pmn.co.nz, greaterauckland.org.nz, thepost.co.nz, nzfirst.nz, teaonews.co.nz, elections.nz, nbr.co.nz, sfo.govt.nz, insurancebusinessmag.com, thepress.co.nz, motu-www.motu.org.nz, privacy.org.nz, maoriparty.org.nz, thestandard.nz, thelawyermag.com, nzier.org.nz, shop.greens.org.nz, berl.co.nz, wellington.scoop.co.nz, womensrightsparty.nz, motu.nz, animaljustice.org.nz, fridayoffcuts.com, medsafe.govt.nz, ruralnewsgroup.co.nz, royalsociety.org.nz, stoppress.co.nz, critic.co.nz, energyresources.org.nz, waikatotimes.co.nz, assets.national.org.nz, ipca.govt.nz, allianceparty.nz, crux.org.nz, action.act.org.nz, helenclark.foundation, assets.nationbuilder.com, nzinitiative.org.nz, igis.govt.nz, conservatives.nz, budget.govt.nz, alcp.org.nz, merch.opportunity.org.nz, ashburtoncourier.co.nz, nzofp.co.nz, shop.opportunity.org.nz, phcc.org.nz, seafood.co.nz, vision.org.nz, action.greens.org.nz, res.cloudinary.com, takeovers.govt.nz, cdn.opportunity.org.nz, niwa.co.nz, cdn.rivercitypress.co.nz, nzpam.govt.nz, southlandtribune.substack.com, tetaitokerauparty.org.nz, constructionnews.co.nz, maxim.org.nz, nzloyal.com, cdn.prod.website-files.com, opunakecoastalnews.co.nz, thekaka.substack.com, companies-register.companiesoffice.govt.nz, infrastructure.org.nz, ohchr.org, pateawaverleypress.com, eeca.govt.nz, unodc.org, rbnz.govt.nz, nzglobaleconomicscontext.substack.com, aniobrien.substack.com, environment.govt.nz, iea.blob.core.windows.net, hasanz.org.nz, tepunaaonui.govt.nz, greystar.co.nz, tewaihanga.govt.nz, theasiaeconomist.substack.com, ruralleaders.co.nz, forestandbird.org.nz, fedcourt.gov.au, familyfirst.org.nz, drugfoundation.org.nz, climatecommission.govt.nz, centreformentalhealth.org.uk, cclponline.org, assets.retirement.govt.nz, assets.publishing.service.gov.uk, asms.org.nz, apt.ch, womensdeclaration.com, apex.org.nz, gov.scot, scionresearch.com, palfree.nz, nzmj.org.nz, stonearrow.co.nz, nzae.substack.com, media.umbraco.io, knowledgeauckland.org.nz, justthebusinessjennyruth.substack.com

Class: the page a New Zealand news outlet publishes an article on, read for one thing: the address of the picture the
page names as its lead image (its `og:image` or `twitter:image`). Arthur, 26 November 2026: "when we open or refresh
the newspaper the images are fetched from the sites"; "we just have a blurb and clicking the item opens the link to
the original"; asked whether the estate should read news pages, which `news-articles.md` said it did not: "Yes, read
the pages". The hosts above are the news register's hosts that no other position names (136 of its 187 on 26
November 2026; the rest keep their own positions). The reader is the board's newspaper tab (products/board/paper.py),
on the local network only (hard limit 13), one article's page when its story is first shown and never again.

1. **Is the page open?** Read without a login, key or cookie of ours. A 403, 429 or 5xx, or a challenge page, is a
   failed read: the story shows no picture and the gate holds the host (hard limit 6; ruling 141). A paywalled page's
   head still names its picture; the article text behind the wall is not sought.
2. **Is storing it lawful copying?** Nothing of the page is stored: the gate reads its head, the picture's address (a
   fact) is kept in `<live>/board/news-pictures.jsonl`, and the page bytes are dropped. The picture itself is never
   fetched by the estate: the viewer's browser loads it from the publisher, as any link to the article would. The
   blurb the paper shows is from the article text the news register already holds (`news-articles.md`).
3. **What terms did we accept?** None; no account, no API key.
4. **What does privacy law, or the statute, limit?** A picture's address names no person. A picture may show one; it
   is the publisher's, shown where the publisher put it, on Arthur's own instrument (ruling 102).

Floor: the gate's (the slowest of its default, a stated crawl delay and the polite floor), per host, one at a time per
host; at most 64 KB of a page is read.
