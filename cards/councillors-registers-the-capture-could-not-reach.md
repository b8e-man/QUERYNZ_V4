# Councillors' registers the first nights' capture could not reach, and why
kind: finding
state: open
use-case: none (step 6.3)
session: councils-1
opened: 2026-10-22

From the 22 October 2026 night (387 register documents held for 42 councils):

1. Off-site storage: Hamilton (`hccpublicdocs.azurewebsites.net`), Tasman (`tasmandc-publicdocs.azurewebsites.net`)
   and Porirua (`storage.googleapis.com`) send their register files to a storage host the position does not name, so
   the redirect was not followed. Name the council's own storage host in the position (not a whole cloud domain),
   then let the capture follow it.
2. Twelve landing pages link no file by the register's name (Gore, Hauraki, Hurunui, Hutt, Mackenzie, New Plymouth,
   Porirua, Rangitīkei, Selwyn, Tasman, Waikato District, Greater Wellington): some list members' files by the
   member's name, some keep the register one page deeper. Look at each page's links by shape and widen
   `REGISTER_LINK` per council, not globally.
3. Two register documents (Otorohanga, Taranaki Regional) answered with a redirect to the same site's `www.` host on
   the first night, before the capture followed same-site redirects; the documents count as asked, so the new address
   is never asked. Clear those two items' "asked" by hand, or let a session ask the two new addresses.
4. Five addresses failed (Taupō, Timaru and Upper Hutt 404; Whakatāne and Otorohanga moved): the monthly ask of the
   landing page refinds Whakatāne; the other four need the council's new address.
