-- registers/party_boards: what later modules read (ruling 72: published under pub, not put on the site and not
-- joined into the links until Arthur rules). One row per board role a party declares on a captured page of its
-- own website, cited to the page's hash, its address and the day captured; and every capture with what was made of it.
CREATE OR REPLACE VIEW pub.party_board_roles AS
SELECT key, document, page, place, party, url, captured_on, last_captured_on, captures, capture_kind, archive_url, shape,
       section, name_as_declared, name, qualifier, role, role_basis, tier, read_from, reader, profile, profile_version,
       loaded_at
FROM party_boards.roles;

CREATE OR REPLACE VIEW pub.party_board_pages AS
SELECT document, ts, url, party, captured_on, capture_kind, archive_url, status, shape, reason, rows, set_aside,
       reader, profile, profile_version, loaded_at
FROM party_boards.pages;
