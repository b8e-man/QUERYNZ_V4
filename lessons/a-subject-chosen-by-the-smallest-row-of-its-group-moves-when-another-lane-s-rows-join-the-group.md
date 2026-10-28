A live test that takes "the group's smallest director row" assumes the group's first rows are directors; when the links read a new view its rows join groups and sort first, so choose by what the test needs, not by position.
area: products/templates, tests, live tests, pub.groups, links, subject choice
paid-for-by: 2026-10-28, fix-products-templates-1 session (rulings 114, 116)

03-banking's twice-liquidated subject was the smallest director row of the
first group sitting on two liquidated companies. After the links read
charity officers, the group's id became a `charities:` row and its first
director row sat on a company never liquidated, so the test that starts
from that director's liquidated company found nothing. The query now asks
for a director row on a liquidated company. The same build made a
namesake star centre on a `building_practitioners:` row, so a reader that
reads one hop sees one namesake (the card on the report walk). Where a
test or a reader leans on which row sorts first, a new lane's rows move it.
