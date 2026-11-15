# Dependency notices and container preparation

`modules.json` records the seven declared Go dependency versions and hashes of
all root license, copying and notice files. Original upstream bytes are preserved
in `dependencies/`. Preparation downloads through Go's module mechanism, verifies
the module cache against go.sum, and compares both file inventories and exact
bytes. Missing modules, changed versions or changed notices fail. The build also
copies the actual Go toolchain LICENSE and records its version/hash in the image.
These are attribution records, not a change to third-party license terms.

The Linux amd64 container uses statically linked CLI binaries and the non-root
Distroless static Debian 12 base, which supplies TLS trust roots and basic runtime
files. Base-image legal material stays in its original locations. The exact-version base source/legal mapping is documented in [BASE.md](BASE.md);
no reproducible whole-image rebuild is claimed.
CI runs unit/contracts with CGO disabled, builds both aliases, scans every retained
image layer, verifies exact copied binary/legal bytes, and runs offline help only.
No service, lease, provider, or integration/e2e flow is started.

Trusted main publishes the qualified image to
`ghcr.io/hyperme-sh/hypermesh-cli/runtime:test`, then pulls it back and compares
image identity. The image revision and registry digest are provenance; TEST uses
the moving tag. No version tags, stable release or visibility change is made.
The default command prints help. Config persistence and credentials are supplied
by the operator when using other commands; no credentials are baked into the image.

The separate history workflow scans all reachable commit/tag/blob objects from
HEAD and fetched origin branches/tags, including deleted historical files, without
executing them. Known ZIP/tar archive extensions retain recursive scanning.
Hidden/deleted refs, unreachable objects, remote LFS content, unknown archive
formats and other registries are outside that scope. Scan output never grants
public clearance by itself; no history is rewritten. Older-image scope and limitations are recorded in
[the historical distribution review](../docs/historical-distributions/README.md). Integration/e2e stays in nightly CI.

The base image is bound to the exact digest inspected in initial PR CI. Build
input digests and action commits do not pin the moving TEST channel. Image
configuration rejects inherited HYPERMESH_/CONDUCTOR_ variables. Registry login
and the package-write token are supplied only to the final publication step;
qualification scripts receive no registry credential.
