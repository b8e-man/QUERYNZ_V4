# The company package carries sole traders, partnerships and trading trusts
default: Not taken
blocks: Nothing
recommendation: The default. Take them only when a product needs them, as their own register
raised: 2026-10-20 by companies-1

The plan says sole traders, partnerships and trusts are not in the monthly
file. The package the old estate loaded does carry them, as NZBN records
with no Companies Office number: 227,984 (`bulk.unincorporated_entities_core_data`:
201,077 registered sole traders, 11,506 partnerships, 2,954 trading
trusts, and closed or inactive ones). Each is a name, type, status and
registration date; no address. A sole trader's name is usually a person's
name.

The lane exports and publishes the companies and the other incorporated
bodies (societies, charitable trust boards, public sector entities,
retirement villages) and leaves these out. Taking them later is one more
table in `OTHER` in `capture.py` and a new export; nothing is rebuilt.
