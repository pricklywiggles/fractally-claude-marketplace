---
name: migrate
description: Use this skill to bring a project's stack-it artifacts from an older layout to the current one: move the generated stack reference out of CLAUDE.md into `docs/stack.md`, add the one-line `AGENTS.md` pointer that every coding agent reads, leave CLAUDE.md as a thin `@AGENTS.md` bridge, and stamp the lockfile with the current `format`. It restructures files and pointers. It never generates or refreshes stack content; the most it writes is the old CLAUDE.md text moved into `docs/stack.md` as a placeholder when there is no lockfile, and document-stack regenerates that. Trigger it whenever someone says "migrate my stack-it files", "bring stack-it docs up to date with the new layout", "move my stack out of CLAUDE.md into AGENTS.md", "my stack-it docs are in the old format", "update the stack-it layout", "upgrade my stack-it artifacts", or when a stack-it stage detects a project whose artifacts are behind the current format. It is a utility skill, not a pipeline stage: it does not identify slots, choose, install, or verify tools, and it does not write the stack documentation itself. Safe to run on a project that's already current; it says so and changes nothing.
---

# Migrate

Bring a project's stack-it artifacts from the layout an older version wrote to the layout the current one expects. This skill **restructures**: it moves generated text out of files it no longer belongs in, creates the pointer files agents read, and stamps the lockfile with the current format. It never generates or refreshes stack content. The most it ever writes is the old CLAUDE.md text moved into `docs/stack.md` as a placeholder, and only when there's no lockfile to regenerate from. `document-stack` owns the content; this skill owns the shape.

It runs two ways: on its own when a user asks, and from `document-stack` when that skill detects a project behind the current format.

## Step 1: Detect the format

Read every signal, then take the highest. Don't stop at the first one you find.

- `docs/stack.md`: it's stack-it's only if it's a regular file, not a symlink, whose **first line is the generated header** carrying `format N`. Read N off that line. A `docs/stack.md` without that header is not ours: stop, show the user what's in it, and ask before touching it.
- `.claude/stack-it/stack.yaml`: its top-level `format` key. A lockfile with no key reads as 1.
- `CLAUDE.md`: a `<!-- stack-it:stack start -->` marker reads as 1. Read `CLAUDE.md` from disk, since Claude Code strips HTML comments from loaded context and the marker won't be visible in a `CLAUDE.md` you already have in context. The start marker alone is enough to read the signal; removing the block still needs the full pair (see **Marker integrity**).

No signal at all means nothing has been written yet, so there's nothing to migrate.

The current format is **2**. If **any** signal reads higher than 2, stop and write nothing: a newer stack-it wrote this project, so tell the user to upgrade the plugin rather than downgrade their files. A newer `decide-stack` can stamp `format: 3` on the lockfile while `docs/stack.md` still says 2, which is why the highest signal wins and the first hit doesn't. Otherwise the project's format is the highest signal you read.

**Marker integrity.** Before removing or replacing anything between markers, confirm the file holds exactly one `<!-- stack-it:stack start -->` followed by exactly one `<!-- stack-it:stack end -->`. If the end marker is missing, the two are out of order, or there's more than one pair, remove and replace nothing: show the user the offending lines and stop. No markers at all means there's no block: skip the removal step and continue.

This detection is shared: `document-stack` Step 1 and `migrate` Step 1 must carry the same rules. Change them in both places or in neither.

With no signal at all there's nothing for this skill to do: say so and stop, because a fresh project just needs `document-stack`. If the project is behind, run each migration below in order, from its format up to the current one, then report.

### Verify the layout at format 2

A format number says which layout the project uses, not that every piece of it landed. When the format is 2, check all of it: no `<!-- stack-it:stack start -->` block in `CLAUDE.md`, the pointer present in `AGENTS.md`, the bridge present (or a recorded decline, or a symlink exception), and the `format` stamp present when `stack.yaml` exists. An `AGENTS.md` symlinked outside the project is a reported layout exception rather than a missing piece: never write through it, say that its target carries no pointer, and carry on. Content missing from inside `docs/stack.md` is not part of this check; regenerating that is `document-stack`'s job, never `migrate`'s.

Re-run only the step that produced the missing piece, and report which one you had to redo. For a leftover old block that means the block-removal step alone, subject to **Marker integrity**; the rescue step never runs when `docs/stack.md` already exists, since its whole purpose is to save text that would otherwise be lost.

If every piece is in place, report that the project is current, list what you checked, and change nothing.

## Migration 1 → 2: out of CLAUDE.md, into docs/stack.md plus an AGENTS.md pointer

Format 1 wrote the agent-facing stack summary into a `<!-- stack-it:stack start/end -->` managed block inside `CLAUDE.md`. Format 2 puts that reference in `docs/stack.md`, points at it from `AGENTS.md` so every coding agent finds it, and leaves `CLAUDE.md` as a one-line bridge.

### Every check first, then the writes

Nothing is touched until all three checks pass. A `stopped:` from this skill must never leave a half-migrated tree, and the only way to guarantee that is to learn everything that can go wrong before the first byte changes.

**Check 1: validate the lockfile.** If `.claude/stack-it/stack.yaml` exists, run `${CLAUDE_PLUGIN_ROOT}/scripts/validate_yaml.py --stage stack .claude/stack-it/stack.yaml`. If it fails, report the validator's output and stop with no edits at all. A broken lockfile is not this skill's to fix, and the rescue step below decides whether to drop the user's only record of the stack based on that file being trustworthy.

**Check 2: marker integrity on CLAUDE.md.** Apply **Marker integrity** from Step 1. A broken pair stops the whole hop here, before anything is written. No markers at all is not a failure: there's simply no block, so the removal step will be skipped and the rest of the hop still runs.

**Check 3: resolve the pointer files.** Before the pointer step and the bridge step, resolve `AGENTS.md` and `CLAUDE.md` to the files they actually are.

- They resolve to the same file, whichever direction the symlink runs: treat them as one file. Write the pointer line once and skip the bridge step entirely, because a file that *is* `AGENTS.md` must never contain `@AGENTS.md`.
- `CLAUDE.md` is a symlink to anything other than `AGENTS.md` (a dotfiles repo, a file shared outside the project): that's an intentional bridge exception. Never write through it. Report where it points and that it doesn't import `AGENTS.md`, and offer to place the import only if the user asks.
- `AGENTS.md` is a symlink to a file outside the project: same rule, don't write through it.

When that foreign `CLAUDE.md` holds the old block, the removal step can't run either: writing through the symlink would edit a file outside the project. Report where it points, say the block is still there, and ask the user whether to remove it at the target. Everything else in the hop still runs.

When the two resolve to one file, note in the report that the block came out of the same file the pointer went into.

### Then the writes, in this order

**1. Stamp the lockfile.** This is the first write, deliberately: it's the one that's cheap to undo and the one whose failure means the rest shouldn't happen. If `.claude/stack-it/stack.yaml` exists, set `format: 2` as the first top-level key, above `project`. If a `format` line is already there with a lower value (an explicit `format: 1`), replace that line rather than inserting a second key. Preserve everything else exactly: key order, comments, quoting, and the `stack` list order, which is the install order. Then revalidate with `${CLAUDE_PLUGIN_ROOT}/scripts/validate_yaml.py --stage stack .claude/stack-it/stack.yaml`. If the revalidation fails, restore the file as it was before the stamp, report that the stamp was not applied, and stop before touching any other file.

**2. Take the old block out of CLAUDE.md.** Remove everything from `<!-- stack-it:stack start -->` through `<!-- stack-it:stack end -->`, markers included, plus one of the surrounding blank lines so the file doesn't end up with a double blank where the block was. Keep the block's text; the rescue step may need it. Everything else in `CLAUDE.md` stays byte for byte as the user left it: their house rules, their deployment notes, their headings, their spacing.

**3. Rescue the old text only if it's the sole record of the stack.** If the lockfile exists and validated, drop the removed text. The lockfile is the source of truth and `document-stack` regenerates from it, so carrying stale prose forward would just be something to overwrite. If there is **no** lockfile, the project's stack was inferred and that block is the only record of it, so write it into `docs/stack.md` (creating `docs/` if needed) with these two lines at the top, then a blank line, then the carried text:

```
> Generated by stack-it document-stack, format 2. Edits are overwritten on the next run.
Moved from CLAUDE.md by migrate; run document-stack to regenerate.
```

Carry the content only. Drop the block's own `> Generated by stack-it's document-stack...` banner along with the markers, so the file ends up with exactly one "Generated by" line. Promote the carried headings one level, since they're moving from a section of `CLAUDE.md` to a file of their own: `## Tech Stack` becomes `# Tech Stack`, `### Commands` becomes `## Commands`. Say in the report that this is a placeholder `document-stack` will overwrite after re-confirming the inference.

**4. Ensure the AGENTS.md pointer.** `AGENTS.md` gets exactly one line from stack-it, verbatim:

```
Before adding a dependency or running the build, test, or lint toolchain, read the stack reference: @docs/stack.md
```

This is a presence check, not a managed block. If `AGENTS.md` already contains `@docs/stack.md` outside backticks, do nothing, even if the sentence around it has been reworded; the pointer is there and the wording is the user's. Otherwise append the line, creating `AGENTS.md` if it's missing and putting a blank line before it if the file already has content. Never add markers to `AGENTS.md`, and never wrap the path in backticks or a code fence: a backticked path isn't an import, so Claude Code would skip it.

**5. Ensure the CLAUDE.md bridge.** Claude Code loads `CLAUDE.md`, not `AGENTS.md`, at session start, so it needs a one-line file that imports the other. Take the first case that matches:

- `CLAUDE.md` doesn't exist, or holds nothing but whitespace: create it containing the single line `@AGENTS.md`. If any text remains, take one of the cases below instead.
- `CLAUDE.md` is a symlink to `AGENTS.md`, or already contains `@AGENTS.md` outside backticks: leave it alone.
- `CLAUDE.md` already contains `@docs/stack.md` outside backticks (the fallback from an earlier declined import): leave it alone.
- `CLAUDE.md` exists with none of those: ask once, "add `@AGENTS.md` at the top of CLAUDE.md? If not, I'll append the pointer line instead so Claude Code still reads docs/stack.md." On yes, add that one line at the top. On no, append the pointer line, under the same presence check and with no markers.

`CLAUDE.md` never gets generated stack content back. The most it ever holds is that one import line or that one pointer line.

## Adding a future migration

Each format bump is one more numbered section, run in sequence until the project reaches the current format. To add 2 → 3: write a `## Migration 2 → 3` section describing only that hop, then bump the current format number everywhere it's stamped:

- Step 1 of this skill.
- `document-stack` Step 1, and the header line in its Step 4a.
- `decide-stack`'s YAML example and the prose under it.
- The input YAML examples in `install-stack` and `scaffold-and-verify`.
- The schema comment in the plugin README.
- The fixture lockfiles and evals under `document-stack`, `migrate`, and `setup-stack`.
- Then run `rg -n 'format[: ]+2' plugins/stack-it` to catch anything this list missed.

Earlier hops keep their own numbers: the 1 → 2 section's heading and its `format: 2` stamp stay at 2. A project at format 1 then runs 1 → 2 and 2 → 3 back to back, which is why each hop must leave the project in a valid state on its own rather than assuming the next one follows.

## Report

Say what actually happened, file by file:

- What changed: the CLAUDE.md block removed, whether its text was carried into `docs/stack.md` or dropped because the lockfile supersedes it, a pointer line appended to `AGENTS.md`, a `CLAUDE.md` that got the `@AGENTS.md` import or the appended pointer line, the `format` stamp written to `stack.yaml`.
- What was created: `docs/stack.md`, `AGENTS.md`, the `CLAUDE.md` bridge.
- What was left alone: a pointer already present, a `CLAUDE.md` that already bridged or already carried the pointer, a symlink you refused to write through, the README.
- The format the project started at and the format it's at now.

End the report with one of two lines, so a caller can tell the outcome without parsing prose: `migrated to N` when the project reached format N, or `stopped: <reason>` when you stopped without finishing (an unowned `docs/stack.md`, a format ahead of this plugin, broken markers, a lockfile that failed validation, a stamp that failed revalidation).

If `document-stack` invoked you, hand back to it; it writes the real content next. If the user ran you standalone and there's no `docs/stack.md` content yet, tell them to run `document-stack` to fill it in.

## Boundaries

This skill restructures stack-it's artifacts and nothing else. It doesn't choose tools (`decide-stack`), install them (`install-stack`), verify them (`scaffold-and-verify`), or write the stack documentation (`document-stack`). It never generates or refreshes stack content: the one exception is moving the old CLAUDE.md text into `docs/stack.md` as a placeholder when no lockfile exists, and even then it copies rather than composes. It never edits content between the README's `<!-- stack-it:stack start/end -->` markers; the README's managed block is already format-2 shaped and stays where it is. It doesn't touch anything in `CLAUDE.md` outside the old managed block, and it doesn't rewrite the user's own words anywhere.

## Bundled resources

- `${CLAUDE_PLUGIN_ROOT}/scripts/validate_yaml.py`: Validate the lockfile before any edit and again after stamping it with `format`, with `--stage stack`. Run `python ${CLAUDE_PLUGIN_ROOT}/scripts/validate_yaml.py --help` for usage.
