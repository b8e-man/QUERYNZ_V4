Mask every Gazette sample before printing it into a session: an independent celebrant's list (Marriage Act, Civil Union Act) prints each celebrant's street address as its third field, so a list of names can be a list of home addresses.
area: Gazette notices, celebrants, reading documents, hard limit 11, hard limit 15, sampling text into a session
paid-for-by: 2026-10-20, gazette session 1, step 4.1

The first look at six celebrant notices printed one civil-union list
whose records read `Surname, Given, 12 Some Street, Suburb, Town.`: home
addresses, into the session, against hard limit 11. After that every look
was a masked shape (capitals to X, digits to 9) or a count. The old reader
(C226) took the same third field for an "organisation", and where the
address began with a number its regex slid on and made the street a
surname: a person who does not exist, built from an address. The reading
now decides per record: a third field holding a number, or a street word
with a town after it, is an address and goes to `gazette_private`; a list
where most records are located is an address list and every third field in
it is private, a bare town included. Two more traps from the same lists: a
street word alone is not an address (Lane, Court, Way and Close are
surnames; The Way is a church), and a few stray stops in a chained list of
thousands do not make it a stopped list: decide the shape by commas per
stop, not by whether stops exist.
