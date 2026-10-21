# The organisation-name rule reaches past the exact filed name
kind: finding
state: open
use-case: 9
session: scan-1
opened: 2026-10-21

The proving scan `donors-named-as-companies` asks for donors whose exact
filed name is a company name, by the links' own rule
(`organisation-name@1`, near). On the real tables the rule's key folds the
legal ending and the country word: "Hero Limited" reaches "HERO
INCORPORATED" (the reason says several companies carry the name), and "THE
NZ LABOUR PARTY DUNEDIN SOUTH BRANCH INC" reaches "THE NEW ZEALAND LABOUR
PARTY DUNEDIN SOUTH BRANCH INCORPORATED". The lines are right as the rule
states them and each carries the rule's reason; but a scan cannot say
"exact" when the rule does not, so the template's limits say so and the
check compares names as the rule does.

What the shape needs from the links: the rule's reason to say which fold
matched (legal ending, "NZ", exact), or a second, stricter rule for the
exact filed name, so a template can choose. Owner: links; the decision
queue already holds "may a company name alone confirm a donor".
