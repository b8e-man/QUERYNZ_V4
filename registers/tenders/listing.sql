-- registers/tenders, the GETS listing as the ingest MCP serves it (listing.py; rulings 96, 138, 142). Rebuilt from
-- the gets corpus's documents at every load, dropped and made again in one transaction. One row per record of the
-- corpus, the version the pull saw last; every field of the record in a column of its own, the page's stable labels
-- too; the contact, the addresses and the page's block whole in the private twin (the tenders schema holds no
-- address).

CREATE TABLE tenders.listing (
    key                     text PRIMARY KEY,       -- the record's `id`: the notice page's address
    rfx_id                  text,                   -- `case_slug`: GETS's RFx ID (the provider's courts reader's name)
    tender_name             text,                   -- `case_name`
    buyer                   text,                   -- `buyer_org`
    tender_type             text,
    reference_no            text,
    close_date              text,                   -- as served
    open_date               text,                   -- as served (from 4 November 2026)
    categories              text,                   -- as served (from 4 November 2026)
    coverage                text,                   -- as served (from 4 November 2026)
    prequalifications       text,                   -- as served (from 4 November 2026)
    listed_as               text,                   -- `discovered_via`: the GETS list the provider found it on (gets_list:open, closed, awarded)
    provider_corpus         text,                   -- `court`: the provider's corpus, always `gets`
    kind                    text,                   -- tender_notice
    url                     text,
    content_type            text,
    page_bytes              bigint,                 -- `bytes`: the captured page's size
    page_sha256             text,                   -- `sha256`: the captured page's hash (the file the record points at)
    provider_path           text,                   -- `path`
    provider_file           text,                   -- `file`
    http_status             integer,
    fetched_at              text,
    arrival_date            text,                   -- `date`: the day the provider took it, not the notice's
    updated_at              text,
    provider_file_uri       text,                   -- `file_uri`: the MCP's address of the record's file (from 5 November 2026)
    provider_tender_id      text,                   -- `tender_id` (from 5 November 2026)
    provider_tender_name    text,                   -- `tender_name` (from 5 November 2026; `case_name` stays in tender_name)
    http_headers            jsonb,                  -- the capture's headers, whole (from 4 November 2026)
    capture                 jsonb,                  -- the capture block, whole
    -- the page's own labels (`page_fields`, from 4 November 2026), each as printed
    page_rfx_id             text,
    page_tender_name        text,
    page_tender_type        text,
    page_open_date          text,
    page_close_date         text,
    overview                text,
    page_categories         text,
    page_coverage           text,
    page_reference          text,                   -- `Reference #`
    page_prequalifications  text,
    department              text,                   -- `Department/Business Unit`
    justification           text,
    indicative_total_value  text,
    project_status          text,
    expected_contracts      text,                   -- `Expected number of contracts offered`
    indicative_release_date text,                   -- `Indicative RFx Release Date`
    -- GETS prints the regions as the label of the field after them: "Regions: Auckland Nelson Exemption Reason"
    regions                 jsonb,                  -- the region names read from that label, in the order printed
    regions_as_printed      text,                   -- the label between `Regions:` and its tail
    regions_unread          text,                   -- words of it no region name matched
    regions_tail            text,                   -- Exemption Reason | Required Pre-qualifications | NULL
    regions_tail_value      text,                   -- the value under that label, as printed
    page_labels_unread      jsonb NOT NULL DEFAULT '[]',   -- any label of the page this reading has no column for
    text_words              integer NOT NULL DEFAULT 0,
    fields_unread           jsonb NOT NULL DEFAULT '[]',   -- any field of the record this reading has no column for
    versions                integer NOT NULL DEFAULT 1,
    seq                     bigint,
    source_note             text NOT NULL,
    document                text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page                    integer NOT NULL DEFAULT 1,
    place                   text NOT NULL,
    read_from               text NOT NULL,
    reader                  text NOT NULL,
    profile                 text NOT NULL,
    profile_version         integer NOT NULL,
    loaded_at               timestamptz NOT NULL
);
CREATE INDEX listing_rfx_id ON tenders.listing (rfx_id);

CREATE TABLE tenders.listing_set_aside (
    item    text NOT NULL,
    stage   text NOT NULL,
    reason  text NOT NULL
);

-- the private twin: the buyer's contact (a person), the addresses, the provider's text and the page's block whole
CREATE TABLE tenders_private.listing (
    key              text PRIMARY KEY,
    contact          text,
    agency_address   text,
    delivery_address text,                          -- `Alternate Physical Delivery Address`
    delivery_fax     text,                          -- `Alternate Physical Fax Number`
    text             text,
    page_fields      jsonb,                         -- every label and value of the page, whole
    document         text NOT NULL
);
