# The report's catalogue knows no charity view, so no template can show a charity arm, its officers or its returns
kind: finding
state: open
use-case: 11 healthcare operator governance; also 2, 8, 9, 14
session: healthcare-1
opened: 2026-10-21

The charities lane's reading (`session/charities-3`, not merged at
2026-10-21 13:30) publishes `pub.charities`, `pub.charity_officers` and
`pub.charity_returns` (the financial fields under the ruling of 14 August
2026). None is on `querynz_v4` yet, `products/report/catalogue.py` has no
View for any of them, and a template naming a view the catalogue does not
know is refused when loaded. So template 11 names the charities register as
not held (`charities`) in its governance and returns sections, and its four
charity flags (`charity-arm`, `charity-returns`, `charity-audit-opinion`,
`charity-return-filed`) and the charity half of `disqualified-officer` are
blocked, never clear. The rules already read the three views by name and
unblock the day the template's `reads` name them.

What the use case needs, after charities-3 merges:

1. For the report lane: three Views. `charities` (`kind="organisation"`,
   title `name`, `start="registered_on"`, `end="deregistered_on"`, status
   in the statement; never `address_for_service` in a statement);
   `charity_officers` (`kind="person"`, names `full_name`, `first_name`,
   `middle_name`, `last_name`, `suppressed="suppressed"`, `start="started_on"`,
   `end="ended_on"`, `role="role"`, `entity=("charities", "charity_key")`;
   `disqualified` and `status` kept on the row; `name_note` as the note);
   `charity_returns` (`kind="figure"`, `on="period_end"` with an on_label
   "period to", `amount="total_gross_income"`, `entity=("charities",
   "charity_key")`). `ROLES_ON["charities"]` gets the officers (by
   `started_on`) and the returns (by `period_end`, newest first); the
   officers into `walk.OFFICER_VIEWS` and `ROLE_VIEWS` so a charity start's
   officers are followed and a person's current charity roles count.
2. For the links lane: charity officers into `pub.names` (so a director and
   a trustee of the same full name join by `full-name@1`), and a charity's
   `nzbn` or `incorporation_number` joined to its companies-register row
   (`official-number@1`, confirmed): the charitable trust board rows
   (35,599 in `pub.companies`, none with an officer) then reach their
   trustees. Without (2) a view the catalogue knows still prints "none
   found" from every start (lesson
   `a-view-no-link-reaches-prints-a-blank-that-is-not-a-clear`).
3. Then template 11 (a fix in its folder): the three views in `reads`
   (licence CC BY 3.0 NZ, attribution "Charities Services, Department of
   Internal Affairs"), `charities` and `charity_officers` in the governance
   section, `charity_returns` in the charity-returns section, the
   `not_held = ["charities"]` lines dropped.

Measured at the checkpoint: two operators' charitable trust boards (Ryman
Healthcare Charitable Trust, Presbyterian Support (Northern)) list no
officer anywhere the report reads, so every officer check on them blocks.
