-- registers/courts (step 5.4; rulings 126 to 128): the courts' documents from the MCP's courts corpus. Two kinds of table:
--   the reading's (documents, cases, case_links, judgments, judgment_parties, paragraphs, people, set_aside, and
--     courts_private.withheld_names): rebuilt from the documents at every load, wiped and refilled in one transaction (load.py);
--   the lane's own record, never wiped: suppression_orders (a ledger a person writes through suppress.py; nothing deletes
--     from it and there is no command that lifts an order).
-- No table here holds an address (hard limit 15). A name a suppression withholds is NULL in judgment_parties and people and
-- kept only in courts_private.withheld_names, which no published view, export or session login reads (hard limit 16).

-- one row per record of the corpus (the version the pull saw last): what became of its file
CREATE TABLE IF NOT EXISTS courts.documents (
    key               text PRIMARY KEY,                -- <record id>  (the record's url)
    record            text NOT NULL CHECK (record ~ '^[0-9a-f]{64}$'),   -- the record document the pointer was read from
    seq               bigint,
    kind              text,                            -- the MCP's kind: case_page | judgment_pdf | media_release
    case_slug         text,
    url               text NOT NULL,
    content_type      text,
    fetched_at        timestamptz,                     -- when the provider captured it
    document          text CHECK (document IS NULL OR document ~ '^[0-9a-f]{64}$'),   -- the file, by hash; NULL when not landed
    state             text NOT NULL,                   -- the pull's: landed | held | caught | waiting
    profile           text,                            -- the profile recognised by shape, or NULL
    profile_version   integer,
    outcome           text NOT NULL,                   -- read | waiting: page reader | waiting: text reader | set aside | caught
    pages             integer,
    read_from         text,                            -- text | pixels | mixed
    text_chars        integer,                         -- characters of text read (text layer, or page readings)
    citation          text,                            -- the neutral citation the document carries, where it carries one
    case_numbers      text[] NOT NULL DEFAULT '{}',
    dated             date,                            -- the date the document prints (judgment, release, hearing)
    summary           text,                            -- the one-line summary the text reader made; NULL until read
    model             text,                            -- the model that made the summary and the people rows
    model_reader      text,                            -- the reader version that asked it
    loaded_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS documents_case_slug ON courts.documents (case_slug);
CREATE INDEX IF NOT EXISTS documents_document ON courts.documents (document);

-- one row per case page read: the court, the case name and the dates the records lack
CREATE TABLE IF NOT EXISTS courts.cases (
    key               text PRIMARY KEY,                -- <document sha256>/case
    case_slug         text NOT NULL,
    url               text NOT NULL,
    case_name         text,                            -- the title before its dash; NULL when withheld
    citation          text,                            -- the citation in the title, where the court printed one
    case_numbers      text[] NOT NULL DEFAULT '{}',
    court             text,                            -- from the breadcrumb: Supreme Court, Court of Appeal, …
    summary           text,                            -- the page's own one-line summary (the court's words)
    result            text,                            -- the page's Result, the court's words
    judges            text,
    date_of_judgment  date,
    date_of_hearing   date,
    suppression       boolean NOT NULL DEFAULT false,
    withheld          text,
    links             integer NOT NULL DEFAULT 0,
    document          text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page              integer NOT NULL,
    place             text NOT NULL,
    read_from         text NOT NULL,
    reader            text NOT NULL,
    profile           text NOT NULL,
    profile_version   integer NOT NULL,
    loaded_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS cases_slug ON courts.cases (case_slug);

-- one row per file a case page links: what the court calls it, and the corpus document it is where the corpus holds it
CREATE TABLE IF NOT EXISTS courts.case_links (
    key               text PRIMARY KEY,                -- <case key>/link/<n>
    "case"            text NOT NULL,
    position          integer NOT NULL,
    section           text,                            -- the heading the link sits under: Decision, Media releases, Hearing Transcripts, …
    label             text,
    href              text NOT NULL,                   -- absolute
    linked_document   text,                            -- the corpus file by hash, where a record points at this url
    document          text NOT NULL,
    page              integer NOT NULL,
    place             text NOT NULL
);

-- one row per judgment document read: the caption's facts, never its text
CREATE TABLE IF NOT EXISTS courts.judgments (
    key               text PRIMARY KEY,                -- <document sha256>/judgment
    citation          text,                            -- the neutral citation as printed: [2024] NZSC 161
    court             text,                            -- NZSC | NZCA | NZHC | NZEmpC | …, from the citation
    court_name        text,                            -- as the court line prints it
    registry          text,                            -- the High Court's registry
    case_numbers      text[] NOT NULL DEFAULT '{}',    -- SC 106/2022, CA274/2022, CIV-…, CRI-…: a consolidated appeal has several
    judgment_date     date,
    date_basis        text,                            -- label | running head | delivered
    hearing           text,                            -- the Hearing: label as printed (dates)
    judges            text,                            -- the Court: label, else the heading's OF …
    heading           text,                            -- JUDGMENT, SENTENCING NOTES, …
    caption_shape     text,                            -- between | criminal | matter | none
    outcome           text[] NOT NULL DEFAULT '{}',    -- a closed vocabulary: appeal dismissed, application granted, …
    paragraphs        integer NOT NULL DEFAULT 0,      -- numbered paragraphs found in sequence
    parties           integer NOT NULL DEFAULT 0,
    suppression       boolean NOT NULL,                -- a banner, an order in the text, or an order in the ledger
    suppression_kinds text[] NOT NULL DEFAULT '{}',    -- banner, order in the text, CPA s 203, Family Court Act, until, paragraphs, ledger
    withheld          text,                            -- why its parties' names are withheld; NULL when none is
    status            text NOT NULL,                   -- parsed | partial | unparsed
    missing           text[] NOT NULL DEFAULT '{}',
    unrecognised      integer NOT NULL DEFAULT 0,      -- caption lines no grammar took: a count, never the lines
    notes             text[] NOT NULL DEFAULT '{}',
    case_slug         text,
    source            text NOT NULL,
    source_url        text,
    source_note       text NOT NULL,
    document          text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page              integer NOT NULL,
    place             text NOT NULL,
    read_from         text NOT NULL,
    reader            text NOT NULL,
    profile           text NOT NULL,
    profile_version   integer NOT NULL,
    loaded_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS judgments_citation ON courts.judgments (citation);

-- one row per party and role a caption names: a consolidated appeal gives one row per party
CREATE TABLE IF NOT EXISTS courts.judgment_parties (
    key               text PRIMARY KEY,                -- <document sha256>/party/<position>
    judgment          text NOT NULL,                   -- judgments.key
    citation          text,
    position          integer NOT NULL,
    block             integer NOT NULL,                -- BETWEEN = 1, each AND one more
    role              text NOT NULL,                   -- as printed: Appellant, First Respondents, Defendant, Prosecutor
    name              text,                            -- as printed; NULL when withheld
    withheld          boolean NOT NULL,                -- the name is withheld (a suppression); the row and its role stay
    anonymised        boolean NOT NULL,                -- the court printed an initial (W, MR N): kept so, never expanded
    crown             boolean NOT NULL,                -- the Crown or a public prosecutor: no suppression covers it
    confidence        text NOT NULL,                   -- high | low (a wrapped list split or rejoined)
    capacity          text,                            -- "as trustees of …", as printed; NULL when withheld
    document          text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page              integer NOT NULL,
    place             text NOT NULL,
    read_from         text NOT NULL,
    reader            text NOT NULL,
    profile           text NOT NULL,
    profile_version   integer NOT NULL,
    loaded_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS judgment_parties_judgment ON courts.judgment_parties (judgment);

-- one row per numbered paragraph, with its page: a citation can say "[2024] NZSC 161 at [45], page 12". No text
CREATE TABLE IF NOT EXISTS courts.paragraphs (
    judgment          text NOT NULL,
    number            integer NOT NULL,
    page              integer NOT NULL,
    document          text NOT NULL,
    PRIMARY KEY (judgment, number)
);

-- one row per person or body the text reader found a document naming, with the role the text gives it (ruling 128):
-- the rows the links lane reads. From a stored model reading only; the load never calls a model
CREATE TABLE IF NOT EXISTS courts.people (
    key               text PRIMARY KEY,                -- <document sha256>/person/<n>
    name              text,                            -- as the document names it; NULL when withheld
    kind              text NOT NULL,                   -- person | body
    role              text NOT NULL,                   -- party | counsel | witness | judge | company | agency | other
    role_text         text,                            -- the role as the text gives it: "counsel for the appellant", "witness for the Crown"
    for_party         text,                            -- counsel: the party acted for, as named in the text
    citation          text,                            -- the document's citation, or its case's
    case_slug         text,
    document_kind     text NOT NULL,                   -- judgment | media release | hearing transcript | counsel submission | case synopsis | case page
    dated             date,                            -- the document's own date
    withheld          boolean NOT NULL DEFAULT false,
    document          text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page              integer NOT NULL,
    place             text NOT NULL,
    read_from         text NOT NULL,
    reader            text NOT NULL,                   -- the lane's model reader and its version
    model             text NOT NULL,                   -- the served model that read it
    profile           text NOT NULL,
    profile_version   integer NOT NULL,
    loaded_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS people_document ON courts.people (document);
CREATE INDEX IF NOT EXISTS people_citation ON courts.people (citation);

-- the catch log: one line for every item the reading could not take, with the stage and the reason
CREATE TABLE IF NOT EXISTS courts.set_aside (
    item     text NOT NULL,                            -- a record id, or a document's hash
    stage    text NOT NULL,                            -- pull | recognise | read | parse | listing
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- a name a suppression withholds, and the capacity printed with it: never published, never exported
CREATE TABLE IF NOT EXISTS courts_private.withheld_names (
    key       text PRIMARY KEY,                        -- judgment_parties.key, people.key or cases.key
    name      text NOT NULL,
    capacity  text
);

-- the ledger of suppression orders the lever records (suppress.py): never wiped, never deleted from
CREATE TABLE IF NOT EXISTS courts.suppression_orders (
    order_id    bigserial PRIMARY KEY,
    citation    text,                                  -- every document of the citation
    document    text CHECK (document IS NULL OR document ~ '^[0-9a-f]{64}$'),
    reason      text NOT NULL,                         -- the order and where it is recorded; never a name
    by_whom     text NOT NULL,
    ordered_at  timestamptz NOT NULL DEFAULT now(),
    CHECK (citation IS NOT NULL OR document IS NOT NULL)
);
