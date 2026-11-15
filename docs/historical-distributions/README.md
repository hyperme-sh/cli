# Older image review scope

CI joins currently tagged Linux amd64 GHCR runtime manifests with digests recorded
in retained successful publication logs. Each selected image is pulled and every
retained layer is inspected and secret-scanned without executing the old image.
No registry tag, visibility setting or historical Git object is changed.

Reports list image user, legal paths and presence of the base source bundle. They
include removed lower-layer files and are not a reconstructed final filesystem.
Earlier images without the new source bundle remain identifiable; a passed secret
scan is not a claim of legal completeness or public redistribution clearance.
Deleted images, unrecorded untagged versions, other architectures/registries and
hidden repository refs remain outside scope. Publication logs select images, never
replace a fresh scan. Results stay in CI logs; there are no Actions artifacts.

Current TEST continues to use the moving runtime:test channel. Integration/e2e
runs remain in nightly CI; this workflow is static content inspection only.
