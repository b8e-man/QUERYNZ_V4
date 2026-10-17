"""keys: the one reading of names, addresses, official numbers and filed
dates (plan step 1.9; contract docs/contracts/keys.md and dates.md).

Pure functions, the standard library only, imported everywhere and copied
nowhere. The old estate had seven name functions and five address keys."""
from keys.addresses import address_key, clean_address, is_po_box
from keys.dates import file_name_date, filed_date, year_from
from keys.names import (PersonName, clean_corporate, fold_diacritics, given_names, is_joint_name,
                        is_organisation, name_kind, organisation_key, person_key, person_name, split_via,
                        strip_honorifics, strip_trailing_comma)
from keys.numbers import charity_number, company_number, nzbn, society_number
from keys.parties import party_name, without_amendment

__all__ = [
    "PersonName", "address_key", "charity_number", "clean_address", "clean_corporate", "company_number",
    "file_name_date", "filed_date", "fold_diacritics", "given_names", "is_joint_name", "is_organisation",
    "is_po_box", "name_kind", "nzbn", "organisation_key", "party_name", "person_key", "person_name",
    "society_number", "split_via", "strip_honorifics", "strip_trailing_comma", "without_amendment", "year_from",
]
