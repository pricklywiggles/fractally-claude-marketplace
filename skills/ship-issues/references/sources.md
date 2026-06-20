# Sources: resolving work-units

Read in Phase 1. A **source** turns the trigger's selection into a normalized list of work-units the rest of the pipeline operates on. The orchestrator picks the source from `config.source.default`; a trigger can override it ("ship the current changes" -> working-tree).

## The work-unit

```
WorkUnit { id?, title?, desc?, branch?, base?, worktree?, url?, prNumber? }
```

`base` defaults to `config.repo.mainBranch`. The diff a stage reasons about is `git diff <base>...HEAD` in the branch/worktree, or the working-tree diff for the working-tree source.

## Selection parsing (tracker sources)

`config.source.tracker.idPrefix` (e.g. `FRA-`) turns bare numbers into ids.
- **status words** ("all todo", "in progress", "backlog") -> every issue in that state.
- **range** ("fra-111-120", "111..120") -> the inclusive range; verify each id exists, drop and report missing ones.
- **explicit list** ("fra-111 fra-112 115") -> exactly those.
- combine freely (a union of the parts).

## Built-in sources

### tracker
Dispatch by `config.source.tracker.type`:

- **`github-issues`** (default): resolve with `gh`. For a status, `gh issue list --state open --label <todo-label> --json number,title,body,url`; for explicit/range, `gh issue view <n> --json number,title,body,url`. Branch name: `<idPrefix><number>-<kebab-title>`, or the issue's linked development branch if set. Carry id (`#<number>`), title, desc (body), url.
- **`linear`**: load the Linear MCP tools (ToolSearch: `list_issues`, `get_issue`). Use `config.source.tracker.project` + `team` and the matching state for status words; `get_issue` each id for range/explicit, reading the **full** description (list truncates). `branch` = the issue's `gitBranchName` (it carries the Linear link, so the merged PR auto-closes the issue). Carry id, title, desc, url.
- **custom**: if `config.source.tracker.type` names a project skill (or `config.source.tracker.resolver` is set), invoke that skill with the selection; it returns work-units in the shape above.

### working-tree
The current changes as one work-unit: `branch` = the current branch (create one off `mainBranch` if you are on it), `base` = `config.repo.mainBranch`, diff = the working-tree and committed-but-unpushed changes. Derive `title`/`desc` from a short description of the change or the branch name. No tracker id.

### branch
A named existing branch as one work-unit: `branch` set, `base` = `mainBranch`, diff = `base...branch`.

### pr
An open PR as one work-unit: `gh pr view <n> --json number,headRefName,title,body,url`; set `prNumber`, `branch`, `title`, `desc`, `url`.

### describe
An ad-hoc task from text: `title`/`desc` from the text; the orchestrator creates the branch per the lane plan. No tracker id.

## Output

A normalized `WorkUnit[]`, passed to Phase 2 (scope + lanes). For tracker sources, each work-unit's `branch` is the tracker's branch name; for the local sources, the orchestrator assigns or creates branches per the lane plan. Resolving issues that do not exist is dropped and reported, never guessed.
