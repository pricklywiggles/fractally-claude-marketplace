---
name: cut-release
description: Cut a new release for this project. Optional and config-gated: analyzes commits since the last published release, proposes a semver bump, writes user-facing notes, opens a version-bump PR, then after merge tags, watches the build, and publishes. Use for "cut a release", "ship a new version", "release vX.Y.Z". Reads config.release; if release management is not enabled it points you at init. Not for shipping issues (use ship-issues) or a single PR.
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion, Skill
---

# cut-release: version, notes, tag, publish

Cut a release end to end: propose the bump, write the notes, open the version PR, and after it merges tag + watch the build + publish. Generic: the version source, tag format, notes style, and build to watch all come from `config.release`.

## 0. Preflight

Load the config (`${CLAUDE_PLUGIN_ROOT}/scripts/load-config.sh`). Release management is **optional**: if `config.release` is absent or `config.release.enabled` is not true, stop and tell the user it is not set up for this project and to run `ship-it:init` to enable it. Otherwise check `gh auth status` and a clean working tree.

## 1. Find the last release and analyze commits

Find the last published release (`gh release list --limit 1`, or the latest tag matching `config.release.tagFormat`). Analyze the commits since: `git log <lastTag>..HEAD`. Group them (breaking changes, features, fixes, chores).

## 2. Propose the bump (checkpoint)

Propose a semver bump from the commits: a breaking change -> major, a feature -> minor, otherwise patch. Compute the new version. Unless a skip-confirmation token is in the trigger, show the proposed version and the grouped commits and confirm with `AskUserQuestion`.

## 3. Write the notes

Write user-facing release notes per `config.release.notesStyle` (e.g. a readable changelog grouped by type, or a user-facing summary). Honor `config.houseRules` (no em dashes, no AI attribution). Save them to a notes file for the release body.

## 4. Open the version-bump PR

Bump the version in `config.release.versionSource` (e.g. `package.json`, `Cargo.toml`, a `VERSION` file), include the notes (a CHANGELOG entry and/or the PR body), and open the PR against the default branch. This is the human gate.

## 5. Post-merge: tag, watch, publish

After the version PR merges, run the publish helper, either by launching the merge-watcher to do it automatically, or by running it once you have merged:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/watch-merges.sh" --prs <version-pr> \
  --reconcile '"${CLAUDE_PLUGIN_ROOT}/scripts/release-publish.sh" --version <new-version> --tag-format "<tagFormat>" --watch-build "<watchBuild>" --notes-file <notes-file>'
```

`release-publish.sh` tags the merged commit (per `tagFormat`), pushes the tag, watches `watchBuild`, and creates the GitHub release with the notes. On timeout or a closed session, run `release-publish.sh` by hand after the merge.

## Guardrails

- Optional and config-gated: never cut a release where `config.release.enabled` is not true.
- Honor `config.houseRules` in the notes, the version commit, and the PR.
- The tag and publish happen only after the version PR merges (the human gate); never on unmerged work.
