-- registers/parliament: what later modules read. Each row cites its document (the record's hash) and the
-- page's own address where the source gives one (`citation_url`; the written questions, bills, reports and SOPs
-- carry none, so they cite Parliament's own id beside the hash). No question, reply or page text is published:
-- it stays in the lane's tables (parliament.written_questions) or its private twin, and the board opens the
-- document whole (ruling 88).

-- one per written question; `member_id` is Parliament's id for the asking member, the id pub.hansard_speeches
-- carries: a join to Hansard is declared by that id, never by a name
CREATE OR REPLACE VIEW pub.parliament_written_questions AS
SELECT w.key, w.document_id, w.question_number, w.question_year, w.parliament_number, w.title, w.member_id,
       w.minister_name, w.ministerial_display_name, w.portfolio_minister_id, w.role_id, w.status_id,
       w.document_type, w.question_released_at, w.question_released_on, w.dated, w.last_modified,
       w.reply_present, w.attachment_id, w.attachment_name, w.attachment_size, w.updated_at, w.provider_fetched_at,
       w.capture, w.served, w.versions, NULL::text AS citation_url, w.source_note,
       w.document, w.page, w.place, w.read_from, w.reader, w.profile, w.profile_version, w.loaded_at
FROM parliament.written_questions w;

-- one per record of the API's bills, select committee calls and reports, and supplementary order papers
CREATE OR REPLACE VIEW pub.parliament_api_items AS
SELECT a.key, a.corpus, a.record_id, a.document_type, a.item_type, a.title, a.short_title, a.bill_title,
       a.bill_number, a.bill_current_stage_name, a.bill_stages, a.select_committee, a.member_name, a.party_name,
       a.author, a.people, a.publication_date, a.publication_on, a.last_stage_date, a.last_modified,
       a.iob_closing_date, a.reference, a.order_number, a.parliament_number, a.sop, a.status,
       a.attachment_id, a.attachment_name, a.updated_at, a.provider_fetched_at, a.provider_collected_at,
       a.capture, a.served, a.versions, a.citation_url, a.source_note,
       a.document, a.page, a.place, a.read_from, a.reader, a.profile, a.profile_version, a.loaded_at
FROM parliament.api_items a;

-- one per archived parliament.nz page; its text is never in a view
CREATE OR REPLACE VIEW pub.parliament_wayback_pages AS
SELECT p.key, p.citation_url, p.snapshot_url, p.archived_at, p.dated, p.html_title, p.doc_type, p.kind,
       p.text_words, p.captured_at, p.captured_sha256, p.capture_status, p.capture, p.served, p.versions,
       p.source_note, p.document, p.page, p.place, p.read_from, p.reader, p.profile, p.profile_version, p.loaded_at
FROM parliament.wayback_pages p;
