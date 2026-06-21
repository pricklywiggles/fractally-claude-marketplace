#!/usr/bin/env bash
# Publish a release after its version-bump PR has merged: tag the merged default
# branch, push the tag, watch the release build, and create the GitHub release with
# the notes. The post-merge step of the ship-it cut-release flow. Generic given the
# version, tag format, build workflow, and notes file.
#
# Usage (run from inside the repo, after the version PR has merged):
#   release-publish.sh --version 1.2.3 --tag-format 'v{version}' [--watch-build release.yml] [--notes-file notes.md]
set -euo pipefail

MAIN="$(git rev-parse --show-toplevel)"
REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
DEFAULT_BRANCH="$(git -C "$MAIN" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || echo main)"

VERSION=""; TAG_FORMAT="v{version}"; WATCH_BUILD=""; NOTES_FILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --tag-format) TAG_FORMAT="$2"; shift 2 ;;
    --watch-build) WATCH_BUILD="$2"; shift 2 ;;
    --notes-file) NOTES_FILE="$2"; shift 2 ;;
    -h|--help) rg '^#' "$0" | rg -v '^#!' | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[ -n "$VERSION" ] || { echo "need --version <semver>" >&2; exit 2; }
tag="${TAG_FORMAT//\{version\}/$VERSION}"

git -C "$MAIN" fetch --quiet origin "$DEFAULT_BRANCH"
if git -C "$MAIN" rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
  echo "tag $tag already exists locally" >&2
else
  git -C "$MAIN" tag -a "$tag" "origin/$DEFAULT_BRANCH" -m "$tag"
fi
git -C "$MAIN" push origin "$tag"
echo "tagged $tag"

if [ -n "$WATCH_BUILD" ]; then
  echo "=== watching build ($WATCH_BUILD) ==="
  run_id="$(gh run list -R "$REPO" --workflow "$WATCH_BUILD" --limit 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || echo "")"
  if [ -n "$run_id" ]; then
    gh run watch "$run_id" -R "$REPO" --exit-status || echo "build watch reported failure (review before announcing)"
  else
    echo "no run found for $WATCH_BUILD yet (it may trigger on the tag); check manually"
  fi
fi

if [ -n "$NOTES_FILE" ] && [ -f "$NOTES_FILE" ]; then
  gh release create "$tag" -R "$REPO" --title "$tag" --notes-file "$NOTES_FILE"
else
  gh release create "$tag" -R "$REPO" --title "$tag" --generate-notes
fi
echo "published release $tag"
