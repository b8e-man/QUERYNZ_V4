# The contracts (plan step 1.9)

Each is a short document here plus a test in the module it binds. They are
the seams every later session builds on; a contract changes only by the
integrator, on a merge request that says why (core: "Merging").

| Contract | Document | Module and test |
| --- | --- | --- |
| The reading of names, addresses and official numbers | `keys.md` | `keys/` |
| Dates | `dates.md` | `keys/dates.py`, `support/rowcontract/` |
| The document store | `document-store.md` | `support/docstore/` |
| The register row | `register-row.md` | `support/rowcontract/` |
| The lane | `lane.md` | `support/lane/` |
| The reader | `reader.md` | `support/reader/` |
| The model client | `model-client.md` | `support/modelclient/` |
| The document profile | `document-profile.md` | `support/profiles/` |
| Links, decisions, groups | `links.md` | `links/` |
| A template | `template.md` | `products/templates/` |
| A job | `job.md` | `support/jobspec/` |
