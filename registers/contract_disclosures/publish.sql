-- registers/contract_disclosures: the published views. Each row carries the licence, the attribution and its
-- citation (the file's sha256, the sheet and the row). No supplier, person or address is in any file read.

-- an agency's published claims and costs through its contract classes, by year, region and territorial authority
CREATE OR REPLACE VIEW pub.agency_contract_costs AS
SELECT key, agency, level, region, territorial_authority, contract_class, financial_year, year_ended,
       active_claims_as_published, total_costs_as_published, active_claims, total_costs_nzd, suppressed,
       licence, attribution, document, page, place, read_from, reader, profile, profile_version
FROM contract_disclosures.costs;
