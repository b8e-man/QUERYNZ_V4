owns: `<live>/llama/bin` (the estate's own copy of the model server, with `VERSION.json`); the placing of `qv4-*` unit files in the user unit folder
reads: the repository's unit files (`checks/jobs/`, `support/*/units/`), `requirements.txt`, the profiles' weights list, the old build at `/home/user/llama.cpp/build/bin` (read only), the credential folder's file names (never their contents)
publishes: nothing; `python -m support.installer check` prints the parity report
outside check: the unit files on the box hash-equal the repository's; the model server copy hash-equal its source; every profile's weights present
jobs: none of its own; it installs the others'
