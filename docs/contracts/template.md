# Contract: a template

**Fixes:** what a use case on a shape is made of. **Test:**
`products/templates/tests/`. **Taken from:** new (design: "Products: four
shapes").

A template is data (`products/templates/<name>.json`), rendered by its
shape, and holds five things:

1. **Which published tables it reads,** each with its licence terms, the
   attribution it requires and how often it must be refreshed. This is
   also all it is allowed to read: `pub.*` views only, never the inside of
   a lane (the one-way test holds this in code).
2. **Its sections, in order.** A section headed "articles mentioning"
   retrieves journalism by keyword and asserts nothing.
3. **Its own rules:** warning flags and patterns.
4. **Its known-limits page:** what the product cannot see, told to the
   reader. An accepted finding becomes a line here.
5. **Its owner and version.**

Rules for everything a product shows: every figure links to its document;
a blank says "none found" or "not held"; a total states what it leaves out;
an unreadable name is shown as unreadable, never hidden, guessed or ranked;
a figure read from pixels is marked as weaker. A product never writes into
the estate. Every product's surface listens on the local network only
(hard limit 13). The Follow the Money template's own settings are fixed in
`docs/plan/design.md` and reproduce the frozen site.
