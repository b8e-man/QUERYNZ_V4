# Contract: the reading of names, addresses and official numbers

**Fixes:** one function each, in `keys/`, imported everywhere and copied
nowhere. **Test:** `keys/tests/`. **Taken from:** the old estate's seven
name functions and five address keys, their rules and their test cases; no
existing copy promoted.

## Names (`keys/names.py`)

1. `person_name(raw)` reads a filed person name: honorifics and
   post-nominals off (the one list), a deceased marker off, the trailing
   comma off, "Family, Given" turned round. Spelling, case and macrons are
   kept as filed. `.display` is the given-first form.
2. `person_key(raw)` is the comparison key: diacritics decomposed (never
   deleted), lower, apostrophes out, punctuation to spaces; a bare two- or
   three-word name is order-free. Nicknames, initials and spellings never
   fold. The key is for equality; nothing fuzzier.
3. `organisation_key(raw)`: lower, possessive and leading "the" off,
   corporate suffixes off, "nz" → "new zealand". " party" is not folded.
4. `is_organisation(name)`: an organisation word anywhere, unless a two- or
   three-word name ends in a weak word and begins with a given name from the
   director register (`keys/given_names.txt`, old ruling 360). `name_kind`
   orders estate, party organ, organisation, person.
5. `is_joint_name(name)`: True for two people filed as one line, False for
   one donor (an organisation with "&" in its name included), None for a
   shape nobody has judged. A joint filed name is one donor.
6. `split_via`: "X via Y" names X; Y is the conduit.

## Parties (`keys/parties.py`)

7. `party_name(label, registered)` → (registered name or None, basis) with
   basis exact, variant, core, fuzzy:0.NN or unresolved; or, given the
   parties lane's name rows and `on`, (registration key or None, basis)
   among the registrations live that day (a year: live at any point in
   it); two live registrations is unresolved. Amendment markers, months
   and years are removed first. A renamed party is the same party. The
   fuzzy arm needs one clear winner and the party's distinctive word
   readable in the label; it never joins two parties. Unresolved is never
   guessed. Without the lane's rows the register list is the snapshot of
   18 October 2026; the live path is beside it (fix-keys-1, 20 October).

## Addresses (`keys/addresses.py`)

8. `address_key(raw)`: letters and digits only, for equality; diacritics
   decomposed, abbreviations one way, "New Zealand" dropped, a PO Box kept
   as `pobox<n>`. Street numbers are kept whole. An address never confirms a
   link on its own (design: "How a link is made").
9. `clean_address(raw)` → (address or None, the date that stood in front):
   the one cleaning every page-read row passes through; a page dump is no
   address.

## Official numbers (`keys/numbers.py`)

10. `nzbn`: 13 digits with the GS1 check digit, else None. `company_number`,
    `society_number`: digits, no leading zeros. `charity_number`: `CC<n>`.
    A missing number is None, never an empty string.

## What this contract does not do

It does not decide identity. Equal keys are evidence for the link rules
(`links/`), which say what confirms and what stays near.
