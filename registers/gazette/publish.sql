-- registers/gazette: what later modules read. Every notice held, typed, with its address; the celebrants read
-- from the Registrar-General's lists. The notice text is never published (bankruptcy and prohibition notices print
-- home addresses), and no address column is: an independent celebrant's address stays in gazette_private.
CREATE OR REPLACE VIEW pub.gazette_notices AS
SELECT key, notice, year, section, number, family, format, status, records, title, published_on, url, source_note,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM gazette.notices;

CREATE OR REPLACE VIEW pub.gazette_celebrants AS
SELECT key, notice, published_on, action, statute, period_from, period_to, surname, given_names, organisation,
       list_shape, marks, split, ordinal, document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM gazette.celebrants;
