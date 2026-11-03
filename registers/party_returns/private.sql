-- registers/party_returns: the private twin. A donor's or lender's street address, and the name-and-address cell it
-- was cut from, keyed by the published row's key; each lender block whole (ruling 142). The session reader and the
-- product login are never granted this schema. Loaded by replacing `party_returns_private.`.
CREATE TABLE IF NOT EXISTS party_returns_private.addresses (
    key        text PRIMARY KEY,                             -- party_returns.donors.key or party_returns.loans.key
    document   text NOT NULL,
    address    text NOT NULL,                                -- the cell after the name, as read
    cell       text NOT NULL                                 -- the whole cell, as read
);

-- each Part H lender block whole, as read (ruling 142, 4 November 2026): the guarantor's name and address, the
-- security and any terms the published loan row does not carry, keyed by the loan's key
CREATE TABLE IF NOT EXISTS party_returns_private.loan_blocks (
    key        text PRIMARY KEY,                             -- party_returns.loans.key
    document   text NOT NULL,
    page       integer,
    block      text NOT NULL                                 -- the block's lines, as read, joined by newlines
);
