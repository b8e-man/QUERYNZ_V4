-- registers/worksafe: what later modules read (plan 5.3, use cases 5, 6 and 7). WorkSafe New Zealand's court
-- summaries (one per prosecution decided) and accepted enforceable undertakings, one row per item WorkSafe lists today
-- (an item it takes down leaves the views at the next load), with the facts as the page states them: the duty holder,
-- the section charged, the decision and its date, the fine and reparation as stated; nothing inferred. One row per duty
-- holder as WorkSafe names it. A name WorkSafe withholds, publishes as a code ('2019-A'), or a page states is
-- suppressed is withheld on every view, with the heading and the page address (hard limit 16). No address of any
-- kind; the facts in brief and the incident (which describe the victim and the place) are never read (hard limit 15).
CREATE OR REPLACE VIEW pub.worksafe_actions AS
SELECT a.key, a.kind,
       CASE WHEN a.title_withheld THEN 'name withheld by WorkSafe' ELSE a.title END AS title,
       a.title_withheld, a.industry, a.offence_when, a.offence_on, a.section_charged, a.acts, a.sections,
       a.charged_when, a.charged_on, a.court, a.plea, a.decision, a.decided_on, a.fine_text, a.fine_amount,
       a.reparation_text, a.status, a.published_on, a.accepted_on, a.action_on, a.url,
       a.document, a.page, a.place, a.read_from, a.reader, a.profile, a.profile_version, a.loaded_at
FROM worksafe.actions a;

CREATE OR REPLACE VIEW pub.worksafe_parties AS
SELECT p.key, p.action_key, p.ordinal,
       CASE WHEN p.withheld THEN 'name withheld' ELSE p.name END AS name,
       p.withheld, p.withheld_by, p.organisation, p.company_number, p.named_in, p.split_from,
       p.document, p.page, p.place, p.read_from, p.reader, p.profile, p.profile_version, p.loaded_at
FROM worksafe.parties p;
