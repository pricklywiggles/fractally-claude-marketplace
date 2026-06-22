---
name: plan-one-issue
description: Plan a single work-unit before any code is written: read its intent, predict the files it touches, and produce a right-sized implementation plan (validating and refining any plan already in the ticket, never discarding it). Read-only; emits a plan plus predicted files and a preliminary doc classification. Use for "plan this issue", "draft a plan for FRA-123", "scope and plan this ticket before coding", "what's the approach for this work-unit". The planning stage of the ship-it orchestrator, and usable standalone on an issue or a described task. Not for implementing (use fix-one-issue), batch-shipping many issues (use ship-issues), review (review-and-address), or just listing issues.
allowed-tools: Bash, Read, Grep, Glob
---

# plan-one-issue: scope and plan one work-unit (read-only)

Take one work-unit's intent and produce a right-sized, reviewable plan the implement stage will build against. Read-only: no edits, no commits, no worktrees. The deliberate planning stage; it runs concurrently (one per work-unit) inside the orchestrator and standalone on its own.

## 1. Resolve the work-unit

- **Orchestrated**: you are given a work-unit (`id`, `title`, `desc`, `branch`, `base`, `url`). Reason read-only against `base` (or the current checkout); do NOT create a worktree.
- **Standalone**: given an issue id, fetch its intent (the default source); given a described task, use the text directly.

## 2. Read config

Load the resolved config via `${CLAUDE_PLUGIN_ROOT}/scripts/load-config.sh`; read keys with `jq`:
- `houseRules` / `safety` (the plan must respect them, e.g. code-only verification, or a "read the framework doc first" rail),
- `planning.depth` (`adaptive` | `light` | `full`; `adaptive` scales depth to complexity),
- `docs.jobs` (their `name` + `appliesWhen`, to classify `docNeed`).

## 3. Gather signal (read-only)

1. Read the work-unit's full intent. If the ticket body already carries a plan, acceptance criteria, or a checklist, treat it as the **seed to validate and refine, never discard it**.
2. Predict the files. If `graphify-out/` exists, query the graph for the relevant nodes and files (the fastest accurate signal). Otherwise explore read-only (Grep/Glob/Read) to locate the exact code the change touches. Scope every search to the working copy.
3. Note any unknown that would change the implementation as an `openQuestion`. Do not ask it here; the orchestrator front-loads questions at its checkpoint, and standalone you surface them in the output.

## 4. Produce the plan (adaptive depth)

Right-size to complexity (`planning.depth` can force it):
- **Trivial** (a one-line or single-call change): a one-sentence plan and the file(s). No ceremony.
- **Normal**: the steps in order, the files each touches, the approach, the risks and edge cases, and how it will be verified (`config.verify`).
- **Thin ticket** (a sentence of intent): author the plan fully from exploration.
- **Ticket already plans well**: validate it against the real code and refine, flagging anything stale or missing; keep the author's structure.

A good plan is the smallest correct change spelled out: what to change, where, and why, with the edge cases that matter. Resolve this work-unit only; do not fold in adjacent cleanups.

## 5. Classify documentation impact (preliminary)

For each `config.docs.jobs`, decide whether the planned change meets its trigger (`appliesWhen`): a user-facing capability / behavior / route / data-path change, a reusable visual or design-system primitive, an architectural decision or boundary shift, and so on. Return the matching job names. This is preliminary: `fix-one-issue` confirms it against the actual change. Most changes are none; do not over-classify.

## Output

- **Standalone**: print the plan, the predicted files, and the doc classification. Note that under the orchestrator the approved plan is posted back to the source (`config.planning.postBack`); offer to post it if asked.
- **Called by the orchestrator**: a structured result, `{ issueId, plan, predictedFiles, docNeed: [...], docRationale, complexity, openQuestions: [...] }`. `plan` is the text the implement stage builds against; `complexity` is `trivial` | `normal` | `complex`; `predictedFiles` feeds lane grouping; `openQuestions` feed the checkpoint.

## Guardrails

- Read-only: never edit, commit, push, or create a worktree. Planning only.
- Stay generic: graphify is an accelerator when present, never a requirement.
- Do not over-plan: trivial work gets a trivial plan; match the ticket's own depth when it already plans well.
- Honor `houseRules` + `safety` in the plan itself (no em dashes, no AI attribution; carry project rails like code-only verification into the verification step).
- Non-interactive: surface `openQuestions` in the result; do not block.
