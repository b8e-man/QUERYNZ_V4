-- registers/tenancy_tribunal (track E): what this lane captured, in its own schema. Capture and hold: the reading
-- comes in step 5. No table here holds a name or an address: the listing's party names and tenancy address are
-- never asked for (the listing is fetched with a field list), and the orders themselves stay in the document store.
-- tenancy_tribunal_private holds nothing yet; a tenancy address, if a reader ever extracts one, goes there (hard limit 15).

-- one row per order PDF the Tribunal lists: what the listing said, and the document once it is landed
CREATE TABLE IF NOT EXISTS tenancy_tribunal.orders (
    order_id           text PRIMARY KEY,                      -- the listing's orderId (one application may have several orders)
    case_id            text NOT NULL,                         -- the listing's id (<application id>_<order id>)
    application_number text NOT NULL,                         -- the Tribunal's application number, as listed
    published_date     date NOT NULL,                         -- when the Ministry published it
    decision_date      date,                                  -- the listing's decision date
    date_of_issue      text,                                  -- the order's date of issue, as listed (dd/mm/yyyy)
    unpublished_date   date,                                  -- when the Ministry takes it down: the end of the three years
    source_url         text NOT NULL,                         -- where the PDF is served
    listing            text NOT NULL CHECK (listing ~ '^[0-9a-f]{64}$'),   -- the listing document this row was read from
    listed_at          timestamptz NOT NULL DEFAULT now(),
    document           text CHECK (document ~ '^[0-9a-f]{64}$'),           -- the order's sha256 once landed; NULL until then
    captured_at        timestamptz
);
CREATE INDEX IF NOT EXISTS orders_pending ON tenancy_tribunal.orders (unpublished_date) WHERE document IS NULL;

-- one row per month of the listing read: the source's own count for that month (check.py) and the listing's hash
CREATE TABLE IF NOT EXISTS tenancy_tribunal.listings (
    month       date NOT NULL,                                -- the first day of the published month
    num_found   integer NOT NULL,                             -- the source's own count for the month, when read
    rows_read   integer NOT NULL,
    listing     text NOT NULL CHECK (listing ~ '^[0-9a-f]{64}$'),
    url         text NOT NULL,
    read_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (month, read_at)
);

-- the catch log: one line for every item the lane could not take, with the stage and the reason
CREATE TABLE IF NOT EXISTS tenancy_tribunal.set_aside (
    item     text NOT NULL,                                   -- an order id, a month, or a URL
    stage    text NOT NULL,                                   -- listing | fetch | land
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);
