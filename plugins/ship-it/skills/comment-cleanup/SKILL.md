---
name: comment-cleanup
description: >-
  Aggressively audit code comments against the user's strict "comments explain
  non-obvious why, never narrate what the code does" standard: delete comments
  that do not earn their place and compress the survivors (two-line ceiling,
  one line preferred). Use this whenever the user asks to review, audit, clean
  up, sanity-check, or justify comments; whenever they ask "did I follow the
  comment rules / our comment guidelines"; right after writing or heavily
  editing code; and before committing or opening a PR. Also use it proactively
  when you have just generated more than a couple of comments. The caller may
  restrict the audit to a path, a function/symbol, a glob, "staged", "the
  branch diff", or "the PR"; if no scope is given, audit only newly written or
  changed code, never the whole repo.
---

# Comment cleanup

One idea drives this skill: **a comment must earn its place by saying something
the code cannot, in as few words as possible.** Comments are read far more
often than written, are never type-checked, and rot silently. A comment that
restates the code is worse than none: the reader must read it, distrust it,
and verify it against the code.

The default verdict is REMOVE. A comment survives only by proving it carries
information the code cannot express, and even then it gets compressed. A
wrongly deleted comment costs one git revert; a wrongly kept one costs every
future reader. When torn between KEEP and TRIM, trim. When torn between TRIM
and REMOVE, remove.

## What survives

Only a non-obvious *why* the code cannot be made to express:

- **Business / domain rule** not derivable from the code ("archived rows
  excluded: the exporter counts them separately").
- **Edge case or workaround** ("WKWebView fires this twice on macOS; second
  ignored").
- **Historical / architectural decision** ("Rust, not config: a runtime env
  var can't drive a compile-time feature").
- **Cross-file or security intent** invisible locally ("pairs with the Rust
  devtools(false) gate; this only removes the in-app entry point").
- **Performance rationale** for code that would otherwise look arbitrary
  ("hoisted out of the row so the memoized child stays stable").
- **Tried-and-rejected alternative**, so it isn't "fixed" back ("red tint is
  invisible on this surface; signal is the text color").
- **Intentional surprising behavior** ("already-pinned is the expected no-op").

Everything else is removed or rewritten. A valid category earns a comment the
right to exist, not the right to its current length.

## Length limits

- **One line is the rule for every comment.** Not a target, the rule.
- **One line means one line within the file's line-length convention**
  (assume ~100 columns when none is configured). Compress content, not
  formatting: a 140-character line is not a one-line comment, it is an
  uncompressed comment dodging the rule.
- **A second line must earn its place the way a KEEP does**: only when the why
  genuinely cannot fit in one line within the column limit after cutting
  every derivable word. A two-line comment is a smell; compress to one
  before conceding two. A legitimate why that will not fit one line wraps to
  two; it never stretches the line.
- **Longer than two lines is exceptional and should almost never happen.**
  The only justification is a why where losing detail would cause a bug: a
  protocol or spec constraint, a non-obvious algorithm invariant, a security
  property. If you write one, every line past the second must independently
  pass the same non-derivability test, and the audit report must call it out.

## Economy of words

Comments are telegrams, not prose. For any comment you keep or rewrite:

- Use the shortest phrasing that preserves the fact. Fragments beat sentences;
  comma splices are fine in comments; drop articles and subjects where the
  result still reads.
- One fact per comment. A second fact is usually narration.
- Cut lead-ins and hedges: "Note that", "This is because", "We do this to",
  "It's important to". Start at the fact.
- **No negative parallelism.** State the fact; the denied alternative is
  implied. "Recharts reads layout at mount" says everything "Recharts reads
  layout at mount, not at print time" says, in half the words.
- Cut connective padding when the clause stands alone: "while", "in order
  to", "so that". "beforeprint fires before the snapshot: charts re-render
  at print width" needs no "while ... can still".
- **Never end with what the code does next.** A trailing remedy clause
  ("...so inspect the body instead", "...so we clear the cache here")
  restates the adjacent code; the why alone is the comment.
- No em dashes (hard user preference). Use a colon, semicolon, or two
  sentences.

Worked example. Before, three lines:

```
# The vendor returns HTTP 200 with an embedded error object when a
# tenant is suspended (ticket VEN-4821, won't fix), so raise_for_status
# cannot detect it; inspect the body instead.
```

After, one line within the column limit, nothing non-derivable lost:

```
# Vendor returns 200 with an error body for suspended tenants; won't fix (VEN-4821).
```

Every dropped word was derivable: "inspect the body instead" is the next line
of code, and "raise_for_status cannot detect it" follows from the 200 status.
Resist keeping derivable clauses by stretching the line; that trades the
two-line smell for a worse one.

## Never narrate the code

A comment describing *what the next lines do* is never acceptable, and this is
not a judgment call to hand back to the user. If the code is unclear without
the narration, the code is the problem: rename a variable or function, extract
a well-named helper, introduce an intermediate named value, or simplify the
control flow. Only irreducibly subtle logic gets a comment, and it explains
*why it must be this way*, not what it does.

Narration to remove (and instead clarify the code):

- `// loop through the users` above a `for` loop.
- `// Admins skip the quota check` above the conditionals that compute exactly
  that. The names should say it.
- `// rounded card with a subtle border` above a class string containing
  `rounded-lg border shadow-sm`.
- A docstring re-listing parameters and their obvious meanings.

When you remove narration, make the code self-explanatory in the same change
and report what you renamed or extracted.

## The per-sentence audit

A valid why does not protect the sentences around it. Audit every sentence and
clause independently; any that narrates implementation, restates a type or
name, or describes language/framework semantics gets cut even when its
neighbor is legitimate. Narration often disguises itself as context:

- "The effect re-runs and rebuilds the map cleanly once those conditions
  clear." (That is just how `useEffect` dependencies work.)
- "Null until the GET returns or a print fetch populates it." (Restates a
  state variable's lifecycle visible from its `setState` call sites.)

The classic failure: a five-line comment whose first sentence is the
irreducible why and whose rest narrates mechanism. That is a TRIM to one line,
not a KEEP. Treat every multi-sentence comment as a TRIM until each sentence
has independently justified itself, and then compress the survivor under the
length limits above.

## Also enforce

- **No commented-out code.** Delete it; version control remembers.
- **No doc-header comments** unless the symbol is genuinely public API or
  feeds an auto-doc generator. Internal helpers get no ceremonial headers.
- **Codebase idiom sets tone, not length.** Match the file's voice, but the
  length limits apply even in a chatty codebase; never add verbosity to fit in.
- Respect project `CLAUDE.md` / `AGENTS.md` comment rules; this skill is their
  enforcement arm, not a competing standard.

## Comments only

This audit edits comments, plus the minimal rename or extract needed to retire
a narration comment. Nothing else. Dead code, unused imports or refs,
misplaced pragmas, suspected bugs: note them in the report as observations and
leave the code alone. Deleting them may be right, but it is not this audit's
call, and mixing it into a comment pass makes the diff unreviewable.

## Out of scope

Do not flag or rewrite:

- **Pre-existing comments only moved** by a refactor in the change under
  review. Audit comments introduced or modified in this work; note moved ones
  as "pre-existing, unchanged" unless the user asks for a whole-file pass.
- **Functional / directive comments** the toolchain consumes: `biome-ignore`,
  `eslint-disable`, `ts-expect-error`, `@ts-ignore`, `prettier-ignore`,
  `noqa`, `nolint`, `# type:` pragmas, codegen markers, shebangs,
  license/copyright headers.
- Comments outside the resolved scope (below).

## Resolving scope

Honor a caller-passed scope literally:

- A **file path or glob**: those files only.
- A **function / symbol / class name**: comments inside that symbol only.
- **"staged"**: `git diff --cached`.
- **"branch" / "branch diff" / "the PR"**: diff vs the base branch (below).
- A **commit range**: that range.

If no scope is given, default to newly written or changed code only: the
uncommitted working tree plus this branch's commits not on main. Never audit
the whole repository by default; that drowns the signal and re-litigates code
the user did not touch.

```bash
# main branch name (fallbacks if not "main")
base=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@' || echo main)
mergebase=$(git merge-base "origin/$base" HEAD 2>/dev/null || git merge-base "$base" HEAD)

git diff "$mergebase"...HEAD            # committed on this branch
git diff                                # unstaged
git diff --cached                       # staged
```

Judge each added comment line in the context of the code it sits on, not from
the comment text alone.

## Workflow

1. **Resolve scope** and collect every in-scope comment. List the skipped
   out-of-scope categories once, with a one-line reason each.
2. **Two passes per comment.** Pass A: any non-derivable why at all? No:
   REMOVE. Pass B: per-sentence audit, then compress the survivor to one line
   (two max).
3. **Verdict:**
   - **REMOVE** (the expected majority): narration, duplication, obvious,
     commented-out code, ceremonial header. If narration masked unclear code,
     also give the rename/extract that retires the comment.
   - **TRIM**: a real why wrapped in narration or slack prose, or any comment
     over the length limit. Give the exact replacement text.
   - **KEEP** (rare): every sentence independently non-derivable AND within
     the length limits. Quote it, name its category.
4. **Final squeeze.** Reread every survivor once more with fresh eyes. Any
   two-line comment gets one more compression attempt toward one line; any
   line over the column limit gets its derivable clauses cut, never a longer
   line; trailing what-the-code-does clauses and "not X" contrast halves go.
   This pass almost always shortens something; if it changed nothing, be
   suspicious that pass B was shallow.
5. **Calibrate before reporting.** If KEEP outnumbers REMOVE, if most
   survivors are two-liners, or if any comment exceeds two lines without an
   audit-report justification, re-run pass B; the audit was too generous.
6. **Apply** the edits (and accompanying code-clarity changes) unless the
   caller asked for analysis only. Comments only, per the rule above. Do not
   ask the user to adjudicate narration; removing it is the rule.
7. Re-run the project linter/formatter on touched files and report the result.

## Output format

Lead with a one-line tally, then a per-comment table, then the skipped list.
Use `path:line` references.

```
Audited 14 comments in <scope>. Verdict: 8 remove, 4 trim, 2 keep.

| Location | Comment (truncated) | Why | Verdict |
|---|---|---|---|
| tree-view.tsx:148 | "hoisted so the memoized child stays stable" | perf rationale | KEEP |
| api/items/route.ts:62 | "title edit. updateItem is the single permission authority" | 1st clause restates handler | TRIM → "updateItem is the single permission authority" |
| tree-view.tsx:864 | "Guests get read-only; members can edit..." | narrates conditionals | REMOVE (names say it) |

Skipped (out of scope): 2 pre-existing comments moved by the refactor
(item-pin.ts:3, tree-view.tsx:861); 1 biome-ignore directive.

Comments removed: 57% (412 chars removed, down from 723). Longest surviving comment: 1 line.
```

If you applied edits, list the files changed and the lint result. If you made
code-clarity changes to retire narration, state exactly what you renamed or
extracted so the diff is reviewable.

## Disposition, not diplomacy

The user does not want borderline calls deferred to them. Narration goes, and
the code is made clear enough to stand alone. Ask only when the *why* itself
is unknown to you (a comment asserts a business rule you cannot verify);
inventing a rationale is worse than removing the comment.
