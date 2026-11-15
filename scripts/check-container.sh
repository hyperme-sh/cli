#!/usr/bin/env bash
set -euo pipefail
image=${1:?Image required}
scratch=$(mktemp -d "${RUNNER_TEMP:-/tmp}/cli-inspect.XXXXXX")
container=
cleanup() { test -z "$container" || docker rm "$container" >/dev/null; rm -rf -- "$scratch"; }
trap cleanup EXIT
docker save "$image" -o "$scratch/image.tar"
python3 scripts/inspect-container.py "$scratch/image.tar" "$scratch/layers"
bash scripts/scan-secrets.sh "$scratch/layers"
container=$(docker create "$image")
docker cp "$container:/usr/share/doc/hypermesh-cli" "$scratch/legal"
diff -r "$RUNTIME_CONTEXT/legal" "$scratch/legal"
for name in hypermesh hm; do
  docker cp "$container:/usr/local/bin/$name" "$scratch/$name"
  cmp "$RUNTIME_CONTEXT/bin/$name" "$scratch/$name"
  docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --entrypoint "/usr/local/bin/$name" "$image" --help >/dev/null
done
