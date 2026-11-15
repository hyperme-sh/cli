#!/usr/bin/env bash
set -euo pipefail
[[ "$GITHUB_EVENT_NAME" == push && "$GITHUB_REF" == refs/heads/main ]]
current=$(gh api "repos/$GITHUB_REPOSITORY/commits/main" --jq .sha)
if [[ "$current" != "$GITHUB_SHA" ]]; then
  echo 'Superseded build; TEST channel unchanged'
  exit 0
fi
test "$(docker image inspect "$QUALIFIED_REF" --format '{{.Id}}')" = "$QUALIFIED_ID"
test "$(docker image inspect "$QUALIFIED_REF" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}')" = "$GITHUB_SHA"
channel="ghcr.io/${GITHUB_REPOSITORY,,}/runtime:test"
: "${DOCKER_CONFIG:?isolated job login directory required}"
trap 'docker logout ghcr.io >/dev/null 2>&1 || true' EXIT
printf '%s' "$GH_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin
docker tag "$QUALIFIED_ID" "$channel"
docker push "$channel"
docker pull "$channel"
test "$(docker image inspect "$channel" --format '{{.Id}}')" = "$QUALIFIED_ID"
echo "$channel tracks validated main $GITHUB_SHA" >> "$GITHUB_STEP_SUMMARY"
