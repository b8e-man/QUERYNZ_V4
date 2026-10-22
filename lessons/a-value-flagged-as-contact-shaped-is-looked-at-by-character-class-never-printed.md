When a check flags a value as shaped like an email or a phone number, look at it by column, length and character classes only: masking its digits still prints an email address in full.
area: any session diagnosing check.contact_shapes or a similar contact-value red; hard limit 11, hard limit 15
paid-for-by: 2026-10-23, fix-registers-iwi-directory-1

The iwi directory's check reported one row whose `website` was phone- or
email-shaped. To see why, the session printed the value with its digits
masked. The value was three email addresses, one of them apparently a named
person's, and they printed whole. They went into no file, row, card or log.
Print `re.sub(r"[A-Za-z]", "a", re.sub(r"\d", "9", v))` or a count of `@` and
digit runs. Never print the value with only one class masked. The lane now
keeps no kept label whose value holds an email or phone shape
(`read.CONTACT_VALUE`).
