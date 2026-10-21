-- registers/fma: what later modules read (plan 5.3, use cases 5, 6 and 7). The Financial Markets Authority's warnings
-- and alerts and its enforcement cases, one row per item the FMA lists today (an item it takes down leaves the views
-- at the next load), and one row per party it names, as published. A name the FMA withholds, or one a page states is
-- suppressed, is withheld on every view: the row stays; the name, heading, summary, outcome and page address (which
-- carry it) do not (hard limit 16). A warning's address, website, email, telephone and bank fields are never read
-- (hard limit 15). A warning is the FMA's caution, not a finding against the party.
CREATE OR REPLACE VIEW pub.fma_actions AS
SELECT a.key, a.kind,
       CASE WHEN a.title_withheld THEN 'name withheld by the FMA' ELSE a.title END AS title,
       a.title_withheld, a.summary, a.published_on AS action_on, a.acts, a.sections, a.outcome, a.outcome_when,
       a.outcome_on, a.names_nobody, a.url,
       a.document, a.page, a.place, a.read_from, a.reader, a.profile, a.profile_version, a.loaded_at
FROM fma.actions a;

CREATE OR REPLACE VIEW pub.fma_parties AS
SELECT p.key, p.action_key, p.ordinal,
       CASE WHEN p.withheld THEN 'name withheld' ELSE p.name END AS name,
       p.withheld, p.withheld_by, p.organisation, p.company_number, p.named_in, p.split_from,
       p.document, p.page, p.place, p.read_from, p.reader, p.profile, p.profile_version, p.loaded_at
FROM fma.parties p;
