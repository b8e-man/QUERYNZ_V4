# The word "profile" carries too many meanings, and the reader-configuration system is about to add more
kind: finding
state: open
use-case: machinery (docs/plan/map.md, "Words used in this plan")
session: integrator
opened: 2026-11-26
module: docs/plan/map.md, support/scheduler, support/profiles, support/recipes

The plan's word list says "Profile has three meanings, so this plan always says which": a document profile (one
kind of document: how to recognise it, what to extract), a hardware profile (what a box has) and a model profile
(a model plus its settings on a graphics card). In practice there are more, under the same word:
- the scheduler's `profiles.toml` holds standing servers (`qwen38-27b`, `flash-next`: a model served under a unit,
  its cards, slots and image) and views on them (`text-reader`, `news-reader`, `review`: what each request says),
  both called profiles and told apart only by `on =`;
- a document profile's `config.model_profile` names a view, not a server;
- the reader-configuration system (Arthur, 26 November 2026: "set up a good system for organising and maintaining
  all this information"; support/recipes) adds the serving record (what a box actually runs, by hash), the recipe
  (how one document profile is read: view, passes, prompts, request, gates) and the golden set and trial that
  measure a recipe;
- "card" and "board" were split the same way once (graphics card, card board, checks board).

What closes it: one entry in the word list for each, with a distinct name and the file that holds it, and the code's
names brought into line where they differ (for example `profiles.toml` [profiles.x] with `on =` read as a view on a
server). Defined before tranche 2 of support/recipes names anything new.
