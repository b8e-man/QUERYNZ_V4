-- registers/parliament: the tables this lane owns, in `parliament` and `parliament_private`.
-- Loaded into a staging or scratch schema by replacing `parliament.` (and `parliament_private.`) with that
-- schema's name (load.sql). Every row is read from one document: a record of one of the ingest MCP's parliament
-- corpora, landed whole by support/mcpsource (rulings 78, 94, 96). The estate never fetched parliament.nz:
-- Arthur's provider captured it off-estate. A record is read from the version the pull landed last; every
-- version is in `files`. Each table's columns are the source's fields under their own names (read.py's maps),
-- text as served, then the lane's own.

-- one per written question of the Parliament API (`parliament-written-questions`), question and reply whole
CREATE TABLE IF NOT EXISTS parliament.written_questions (
    key                      text PRIMARY KEY,           -- the API's `id`
    question_number          integer,                    -- `questionNumber`: numbered afresh each year
    question_year            integer,                    -- `questionYear`
    parliament_number        integer,                    -- `parliamentNumber`
    document_id              text,                       -- `writtenQuestionsDocumentId` (WQ_<number>_<year>): Parliament's own id for the page
    title                    text,                       -- `title`: "<number> (<year>). <member> to the <minister>"
    question_text            text,                       -- `questionText`, whole
    reply_text               text,                       -- `replyText`, whole; empty until answered
    member_id                text,                       -- `memberId`: Parliament's id for the asking member (the id hansard's turns carry)
    minister_name            text,                       -- `ministerName`, as the API gives it
    ministerial_display_name text,                       -- `ministerialDisplayName`: the minister's title
    portfolio_minister_id    text,                       -- `portfolioId_PortfolioMinister`
    role_id                  text,                       -- `roleId`
    status_id                integer,                    -- `statusId`, the API's code
    document_type            text,                       -- `documentType`
    question_released_at     text,                       -- `questionReleasedDate`, as served
    dated                    text,                       -- `date`, as served
    last_modified            text,                       -- `lastModified`, as served
    attachment_id            text,
    attachment_name          text,
    attachment_size          integer,
    provider_corpus          text,                       -- the provider's `_corpus`
    provider_fetched_at      text,                       -- the provider's `_fetched_at`: when it took the record
    provider_shard           text,                       -- the provider's `_shard`
    updated_at               text,                       -- the MCP's: moves when the record changes
    capture                  jsonb,                      -- the provider's capture block, whole, where it gives one
    annotation               jsonb,                      -- the provider's annotation block, where it gives one
    question_released_on     date,                       -- the day of `questionReleasedDate` (a midnight-UTC stamp)
    reply_present            boolean NOT NULL,           -- `replyText` holds more than whitespace
    text_words               integer NOT NULL DEFAULT 0, -- words in the record's `text` (the provider's run of its fields, not kept)
    fields_unread            text[] NOT NULL DEFAULT '{}',
    versions                 integer NOT NULL DEFAULT 1,
    seq                      bigint,                     -- the MCP's place for the version read (NULL: no arrival row)
    served                   boolean NOT NULL,           -- false: the MCP no longer serves the record (it removed it)
    source_note              text NOT NULL,
    document                 text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page                     integer NOT NULL DEFAULT 1,
    place                    text NOT NULL,
    read_from                text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader                   text NOT NULL,
    profile                  text NOT NULL,
    profile_version          integer NOT NULL,
    loaded_at                timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS parliament_wq_number ON parliament.written_questions (parliament_number, question_year, question_number);
CREATE INDEX IF NOT EXISTS parliament_wq_member ON parliament.written_questions (member_id);

-- one per record of the API's document corpora: bills (current and historical), select committee calls for
-- submissions and reports, supplementary order papers. Typed by corpus and `documentType`; the bill, stage,
-- committee, member and party as the API gives them. A bill is in both bill corpora: a row in each
CREATE TABLE IF NOT EXISTS parliament.api_items (
    key                      text PRIMARY KEY,           -- <corpus>/<the API's id>
    corpus                   text NOT NULL,
    record_id                text NOT NULL,              -- the API's `id`
    document_type            text,                       -- `documentType`: Bill, SelectCommitteeReport, …
    item_type                text,
    item_sub_type            text,
    title                    text,
    short_title              text,
    bill_title               text,
    bill_number              text,
    bill_current_stage_name  text,
    bill_current_stage_code  text,
    bill_current_stage_id    text,
    bill_stage               text,
    bill_stages              jsonb,                      -- `billStages`, whole
    select_committee         text,
    member_name              text,
    party_name               text,
    author                   text,
    people                   jsonb,
    publication_date         text,                       -- as served
    last_stage_date          text,                       -- as served (a UTC stamp; its NZ day is not taken here)
    last_modified            text,
    iob_closing_date         text,                       -- `iobClosingDate`: when submissions close, as served
    dated                    text,
    reference                text,
    url                      text,                       -- `url` as served (a path on parliament.nz, where given)
    title_url                text,
    attachment_id            text,
    attachment_name          text,
    duration                 text,
    order_number             integer,
    parliament_number        integer,
    sop                      integer,                    -- the SOP's number
    state                    text,
    status                   text,
    subject                  text,
    shoulder                 text,
    thumbnail_url            text,
    text                     text,                       -- the record's `text`: the provider's run of its fields, short
    provider_collected_at    text,                       -- the provider's `_collected`
    provider_corpus          text,
    provider_fetched_at      text,
    provider_shard           text,
    updated_at               text,
    capture                  jsonb,                      -- the provider's capture block, whole: the record's citation
    annotation               jsonb,
    publication_on           date,                       -- the day of `publicationDate` (a midnight-UTC stamp)
    citation_url             text,                       -- the page's own address where the record gives one; NULL where none
    text_words               integer NOT NULL DEFAULT 0,
    fields_unread            text[] NOT NULL DEFAULT '{}',
    versions                 integer NOT NULL DEFAULT 1,
    seq                      bigint,
    served                   boolean NOT NULL,
    source_note              text NOT NULL,
    document                 text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page                     integer NOT NULL DEFAULT 1,
    place                    text NOT NULL,
    read_from                text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader                   text NOT NULL,
    profile                  text NOT NULL,
    profile_version          integer NOT NULL,
    loaded_at                timestamptz NOT NULL
);

-- one per archived parliament.nz page (`parliament-wayback`), taken by the provider from the Internet Archive.
-- The page's text is in the private twin
CREATE TABLE IF NOT EXISTS parliament.wayback_pages (
    key                      text PRIMARY KEY,           -- the record's `id` (the page's address as archived)
    url                      text NOT NULL,              -- the page's own address on parliament.nz
    snapshot_url             text,                       -- the archive's copy the provider read
    ts                       text,                       -- the archive's stamp, as served
    dated                    text,                       -- `date`, as served
    html_title               text,
    doc_type                 text,
    kind                     text,
    bytes                    integer,
    content_encoding         text,
    captured_sha256          text,                       -- the provider's hash of what it received
    captured_at              text,                       -- the provider's `fetched_at`
    capture_status           text,                       -- the provider's `status`
    provider_path            text,                       -- a name on the provider's box
    snapshots                integer,
    provider_corpus          text,
    provider_fetched_at      text,
    provider_shard           text,
    updated_at               text,
    capture                  jsonb,
    annotation               jsonb,
    archived_at              text,                       -- `ts` as an ISO stamp (UTC, as the archive keeps it)
    citation_url             text NOT NULL,              -- the page's own address
    text_words               integer NOT NULL DEFAULT 0, -- words of its text (private)
    fields_unread            text[] NOT NULL DEFAULT '{}',
    versions                 integer NOT NULL DEFAULT 1,
    seq                      bigint,
    served                   boolean NOT NULL,
    source_note              text NOT NULL,
    document                 text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page                     integer NOT NULL DEFAULT 1,
    place                    text NOT NULL,
    read_from                text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader                   text NOT NULL,
    profile                  text NOT NULL,
    profile_version          integer NOT NULL,
    loaded_at                timestamptz NOT NULL
);

-- every document: each version of each record, and which one the row is read from
CREATE TABLE IF NOT EXISTS parliament.files (
    sha256      text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    corpus      text NOT NULL,
    record_id   text,
    seq         bigint,
    status      text NOT NULL CHECK (status IN ('read', 'older version', 'set aside')),
    PRIMARY KEY (sha256, corpus)
);

-- the catch log: one line per item not read (stage, reason); the pull's own catch lines at stage `pull`
CREATE TABLE IF NOT EXISTS parliament.set_aside (
    item    text NOT NULL,
    stage   text NOT NULL,
    reason  text NOT NULL
);

-- an archived page's text as served: never published (an old page may print a person's details; the board
-- opens the document whole, ruling 88)
CREATE TABLE IF NOT EXISTS parliament_private.wayback_texts (
    key   text PRIMARY KEY,
    text  text
);
