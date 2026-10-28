# The board's own files under /static/ (ruling 100)

Served by the board itself (`assets.py`, `GET /static/<name>`), from the
fixed list in `assets.FILES` and nothing else, with a long cache header;
each address carries the file's hash. The page asks nothing of any other
address (hard limit 13; hard limit 10's spirit), and every page's content
security policy says so (`server.POLICY`).

## Vendored, at pinned versions (all three MIT)

The same versions the old estate's graph page locked
(`/home/user/qnz3-ref/gui/package-lock.json`). Each file was taken from its
package's npm registry tarball, read from this box's npm cache, where a
tarball is stored under its own sha512; that sha512 was checked against the
registry's integrity value in the old lock file before the tarball was
opened (26 October 2026, session board-7). The sessions' command list
refuses `curl`, so the jsdelivr address below was not fetched; it names the
same file of the same published package.

| File | Package | Version | From the tarball | Tarball (registry) | Tarball sha512 (registry integrity) | File sha256 | Licence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `cytoscape.min.js` | cytoscape | 3.34.0 | `package/dist/cytoscape.min.js` | https://registry.npmjs.org/cytoscape/-/cytoscape-3.34.0.tgz | `sha512-62rNSrioXw93uliKFBwjukeQyeWwH2PqDrTac31r2P6464u3AUvTk0xS4LVvT251g7IgkFunrI48ZEZGjywSOg==` | `9c2a3bf2592e0b14a1f7bec07c03a54f16dedf32af9cd0af155c716aa6c87bc3` | `LICENSE.cytoscape` (MIT) |
| `cytoscape-cola.js` | cytoscape-cola | 2.5.1 | `package/cytoscape-cola.js` | https://registry.npmjs.org/cytoscape-cola/-/cytoscape-cola-2.5.1.tgz | `sha512-4/2S9bW1LvdsEPmxXN1OEAPFPbk7DvCx2c9d+TblkQAAvptGaSgtPWCByTEGgT8UxCxcVqes2aFPO5pzwo7R2w==` | `bb820d9f649827582d005682e26a0cea915539a0dbda32a17964ad2210bbcd08` | `LICENSE.cytoscape-cola` (MIT) |
| `cola.min.js` | webcola | 3.4.0 | `package/WebCola/cola.min.js` | https://registry.npmjs.org/webcola/-/webcola-3.4.0.tgz | `sha512-4BiLXjXw3SJHo3Xd+rF+7fyClT6n7I+AR6TkBqyQ4kTsePSAMDLRCXY1f3B/kXJeP9tYn4G1TblxTO+jAt0gaw==` | `b45eba3fb02d22d9ea9a2bcad07ddbec8296f807f05e96f8c9d4abbc497f65c7` | `LICENSE.webcola` (MIT) |

The same files on jsdelivr: https://cdn.jsdelivr.net/npm/cytoscape@3.34.0/dist/cytoscape.min.js,
https://cdn.jsdelivr.net/npm/cytoscape-cola@2.5.1/cytoscape-cola.js,
https://cdn.jsdelivr.net/npm/webcola@3.4.0/WebCola/cola.min.js.

Each licence file is the package's own `LICENSE`, beside the file it covers.
`tests/test_canvas.py` holds every sha256 above against the file.

## The board's own

- `webcola-name.js`: WebCola names itself `cola`; cytoscape-cola looks for `webcola`.
- `graph.js`: the canvas (ruling 100) of the graph beside the search tab's results (rulings 108, 111; the graph tab left the bar).

To change a version: replace the file and its licence, update this table
and the test's sha256 in the same commit.
