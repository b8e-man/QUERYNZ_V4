A container image is named by its image id, never by its repository digest: one image copied by save and load carries another digest on the second box, so a digest says how the image travelled, not what runs.
area: model servers, containers, serving records, both boxes
paid-for-by: 26 November 2026, the cutover to the 27B; I told Arthur the boxes ran different Radiance builds

`podman image inspect --format '{{.Digest}}'` gave node2 e648ec53… and node1 0af4867d… for docker.io/stilldeadcode/radiance:latest, and I reported two different builds. The image id (9b45b225…) is the same on both; node1's copy came by `podman save | load`, which gives it a digest of its own. support.recipes.serving records `{{.Id}}`. Two boxes are compared by the id before anyone is told they differ.
