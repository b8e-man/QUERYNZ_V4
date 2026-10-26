# Publish the written questions' question and reply text in pub.parliament_written_questions?
default: No. The text is held whole in parliament.written_questions and opens with the document on the board (ruling 88); the view carries the number, year, member id, minister, dates and whether replied. A question or reply sometimes names a member of the public or a place, and no address check runs over the text yet
blocks: Nothing in the build; a product that searches the questions' words reads the view
recommendation: Yes, once an address-shape check over both columns (the lesson on searching every published column) runs at the load and reports by key; it is a two-column change to publish.sql
also: the API gives no page address for a written question, bill, report or SOP; the rows cite the document hash and Parliament's own id (WQ_<number>_<year>) and no address is made up. Building one from the id needs a pattern the estate can check, and it may not fetch parliament.nz
raised: 2026-10-27 by parliament-1
