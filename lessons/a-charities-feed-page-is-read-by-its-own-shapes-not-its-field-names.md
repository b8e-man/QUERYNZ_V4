Read the Charities feed by what each set's values actually index: a group's MainActivityId points into the 12,728-row Activities set while an organisation's points into the 11-row MainActivity list, one charity number can sit on two Organisations rows, and the same code Id repeats per EntityName.
area: charities, odata, code lists, keys, reading registers
paid-for-by: 2026-10-21, charities-a session (Fable), step 4.1

Three traps met on the first reading of the captured feed, each invisible
from the field names and the data dictionary (which lists fields, not
meanings):

1. Groups' MainActivityId, MainSectorId and MainBeneficiaryId hold ids in
   the thousands (8358, 1230, 6627): they index the keyed Activities,
   Sectors and Beneficiaries sets (the ones that hold every "Other - ..."
   entry a charity typed), not the Main* lists the Organisations set uses.
   Resolve a group's code through the keyed set first, then the list.
2. Nine charity numbers sit on two Organisations rows each (different
   OrganisationIds, the same CC number). Key on the number as the register's
   own, keep the later-modified row, log the other, and attach the dropped
   row's officers and returns to the row kept: they are that charity's.
3. The RegistrationStatus, MainActivity, MainSector and MainBeneficiary lists
   repeat each Id once per EntityName (Groups, Organisations), so a codes
   table keyed on (list, id) collides; key on the entity name too.

Also: dates arrive as `2013-06-17T00:00:00Z` (not the OData `/Date(ms)/`),
five Organisations rows have no number, name or status (blank rows), 61
annual returns name neither an organisation nor a group, the AnnualReturn
set is 3.9 GB of JSON for 430,522 rows (every row carries about 250 fields,
44 of them non-null numerics on average), and reading the whole copy in
Python takes about a minute.
