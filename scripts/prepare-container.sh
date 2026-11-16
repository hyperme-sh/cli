#!/usr/bin/env bash
set -euo pipefail
: "${RUNTIME_CONTEXT:?Disposable build context required}"
export CGO_ENABLED=0
go vet ./...
go test ./...
mkdir -p "$RUNTIME_CONTEXT/bin"
go build -trimpath -o "$RUNTIME_CONTEXT/bin/hypermesh" ./cmd/hypermesh
go build -trimpath -o "$RUNTIME_CONTEXT/bin/hm" ./cmd/hm
python3 scripts/prepare-notices.py "$RUNTIME_CONTEXT/legal"
cp Dockerfile "$RUNTIME_CONTEXT/Dockerfile"
image="hypermesh-cli:ci-$GITHUB_RUN_ID-$GITHUB_RUN_ATTEMPT"
docker build --build-arg SOURCE_SHA="$GITHUB_SHA" -t "$image" "$RUNTIME_CONTEXT"
bash scripts/check-container.sh "$image"
echo "QUALIFIED_REF=$image" >> "$GITHUB_ENV"
echo "QUALIFIED_ID=$(docker image inspect "$image" --format '{{.Id}}')" >> "$GITHUB_ENV"
