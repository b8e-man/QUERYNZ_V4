Under a stated suppression, withhold a party string unless it is one organisation alone: "X Limited and A Person" passes an organisation test.
area: regulator actions, suppression, withheld names, hard limit 16, keys.names.is_organisation
paid-for-by: 2026-10-21, regulators-1, step 5.3

Regulators often publish two parties in one field without a separator ('Mohawk Industries, Inc. Godfrey Hirst New
Zealand Limited and Bremworth Limited'), and a lane splits on ' and ' only between two names that each carry a legal
ending, so a company joined to a person stays one string. `is_organisation` says yes to it. The first rule ("a stated
suppression withholds a party with no organisation word") would have shown the person. The rule in the three
regulator lanes: withheld unless `is_organisation(name)` and the name has no ' and ' or '&' in it; a mutant test holds it.
