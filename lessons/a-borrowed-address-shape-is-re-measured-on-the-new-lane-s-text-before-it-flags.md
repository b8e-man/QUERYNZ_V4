A borrowed address shape is re-measured on the new lane's own text before it flags: Parliament writes "at 5 schools", "Alert Level 4" and "in 2019", which the Gazette's notice-shaped "at <number>" and bare house number would have flagged.
area: hard limit 15, address flags, published text, registers/parliament, shapes copied between lanes
paid-for-by: 2026-10-27, fix-registers-parliament-1 (rulings 101, 102)

The Gazette's three shapes (street, legal, numbered) were written for
notices, where "at 12" is nearly always a house. Parliament's questions
and replies count things after "at", number alert levels, phases, stages
and questions before capitalised words, and open sentences with years. So
the parliament lane's copy (registers/parliament/shapes.py) needs a
capitalised name after a numbered shape's number, and refuses a year or a
number led by Level/Phase/Stage/Question/Bill as a house. Measure the copy
on the full build by column and shape, and characterise the hits by token
class (the placing word, whether the next word is a dictionary word),
never by printing a value. And test the database's second pattern against
the lane's `shape()`, not its bare street regex: the company exemption
("12 Sample Street Limited") lives in `shape()`.
