> Superseded: runtime images no longer download or include source archives.
> LICENSE/NOTICE and dependency legal texts remain. The records below describe
> prior builds and are retained for historical review, not current build steps.

# Reviewed base sources and legal material

The exact Linux amd64 Distroless base is identified by its manifest digest and
12 uncompressed layer identities in `licenses/base-image.json`. Its five Debian
package status records identify base-files 12.4+deb12u15, netbase 6.4, tzdata
2026b-0+deb12u1, media-types 10.0.0 and ca-certificates 20250419~deb12u1.

This container includes the complete Debian source archives, Debian patches and
source descriptors for those versions. Source archive checksums were taken from
the corresponding Debian source descriptors. The older CA-certificates source is
retained at Debian's timestamped archive. CI checks exact download sizes/hashes,
the base layer prefix, package status bytes and installed copyright bytes. Each
installed copyright matches the corresponding source archive member byte-for-byte.
The original common license texts remain under /usr/share/common-licenses.

Distroless-generated passwd/group, directory layout, nsswitch configuration and
OS identity files are retained in the bound base layers. A hash-bound upstream
Distroless source snapshot supplies Apache-2.0 terms and reference build recipes.
CI verifies that its Debian 12 lock names all five installed package versions.
That snapshot is a matching recipe reference, not an attestation of the base's
original build commit. No bit-identical rebuild or complete build-provenance claim is made.
Source and legal records are not blanket public redistribution clearance.

Copy /usr/share/doc/hypermesh-cli/base-sources from a distributed container to
obtain these materials without running the CLI. Exact build-input identities do
not pin the moving GHCR runtime:test channel. Registry/repository visibility and
history are unchanged; integration/e2e remains scheduled nightly CI.

The source scan reports 222 upstream lockfile package identifiers as generic API
key matches. They are public package names, not credentials. Classification binds
the full archive/member hashes, exact scanner rule and line. Changed sources,
new coordinates and runtime files remain failures.
