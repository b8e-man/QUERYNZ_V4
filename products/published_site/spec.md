owns: the published-site shape (plan 4.4): the release pipeline behind the new contract and its gates, without its last steps; it writes a version folder and stops; no deploy step, no deploy token, no draining of the live site's feedback; its preview on ports other than 8300 and 8301, on the local network only
reads: the `pub` views and `products/templates/ftm/` (the Follow the Money template); never a lane's inside
publishes: nothing in `pub`; a version folder of the ten kinds of published file, figure by figure, for the comparison in `checks/` (plan 4.5)
outside check: a version folder built from a frozen release's recorded listing carries every file of the ten kinds; a build with no document store at hand fails plainly
jobs: a `qv4-site-build` job on the scheduler once the pipeline writes a version folder; it never touches the frozen product's publisher job or its ports
