# stack-it

Take a project from nothing to a working, verified, documented tech stack: a guided, resume-aware orchestrator plus five standalone, individually callable stage skills.

## The pipeline

```
identify-stack-slots → decide-stack → install-stack → scaffold-and-verify → document-stack
                          ▲                                   │
                          └──────── stack fault ──────────────┘
```

| Skill | Role |
|---|---|
| `setup-stack` | **Orchestrator.** Runs the whole pipeline, resuming from wherever the project already is, pausing only at the real decision points. |
| `identify-stack-slots` | Derive the decision categories (slots) the project needs. |
| `decide-stack` | Research and pick version-pinned, security-vetted tools for each slot. |
| `install-stack` | Install the locked stack. |
| `scaffold-and-verify` | Build the smallest vertical slice that exercises every tool and run it green (build, lint, tests, dev server, browser console). |
| `document-stack` | Document the stack for agents (`docs/stack.md`, pointed at from `AGENTS.md`) and humans (README). |

Each stage is usable on its own; `setup-stack` is for taking the whole journey in one pass.

## Utility skills

| Skill | Role |
|---|---|
| `migrate` | Bring a project's stack-it artifacts from an older `format` to the current one. Called by `document-stack` when it finds an old layout, and callable on its own. It restructures files and pointers. It never generates or refreshes stack content: the most it writes is the old CLAUDE.md text moved into `docs/stack.md` as a placeholder when there's no lockfile. |

## The living lockfile

The stages share state through two files under **`.claude/stack-it/`** in the project:

- `slots.yaml`: written by `identify-stack-slots`, read by `decide-stack`.
- `stack.yaml`: written by `decide-stack`; read by `install-stack`, `scaffold-and-verify`, and `document-stack`.

`stack.yaml` is the single source of truth. `install-stack` and `scaffold-and-verify` **update it in place** to match reality (a nearest-patch install, a pin-drift fix). What they will *not* do is silently change *which tool* fills a slot: a genuine **stack fault** (a chosen tool that can't work) is escalated back to `decide-stack` and the user, so the lockfile never drifts from the user's decisions.

## The schema contract

Both files are validated by a single bundled script, referenced from every skill as
`${CLAUDE_PLUGIN_ROOT}/scripts/validate_yaml.py` (one copy, no drift). Use `--stage slots` or `--stage stack`.

**slots** (`--stage slots`):

```yaml
project:
  description: <non-empty string>
  type: <non-empty string>        # e.g. cli, web-app, api-service, library
  platforms: [<list>]
slots:
  - slot: <non-empty string>      # a category ("web framework"), never a product
    required: <true|false>
    rationale: <present>
    preference: <tool the user already wants, or null>
    source: <authority that motivated the slot, or null>
```

**stack** (`--stage stack`):

```yaml
format: 2                                    # layout version of stack-it's files; decide-stack always writes it, absent (older files) means 1
project: { description, type, platforms }   # as above
stack:                                       # list order IS the install order
  - slot: <non-empty string>
    choice: <non-empty string>               # the chosen tool
    version: "<exact pinned version, quoted>"  # quote it: `3.10` unquoted parses as 3.1
    install: ["<non-empty step>", ...]        # non-empty list of non-empty steps, verbatim from the version's official docs
    caveats: [<list>]                         # [] for none
    notes: <string or null>                   # e.g. the source doc URL the install steps came from (provenance)
```

`format` stamps the layout of everything stack-it writes, which is not the plugin's version and not the stack's. `decide-stack` always writes the current value, the later stages carry it through when they rewrite the file, and `migrate` brings a project that's behind up to it. Only files written before the stamp existed lack the key, and those are format 1.

The validator checks **shape, not meaning**: it won't catch a `slot` that's accidentally a product name, or a wrong-but-valid version. Those stay the skills' responsibility.

## Developing

Run the validator's unit tests:

```bash
uv run --with pyyaml --with pytest pytest plugins/stack-it/scripts/test_validate_yaml.py
```

Each skill's `evals/` holds its test fixtures and `evals.json`. Heavy behavioral evals (real installs, browser runs) are run out-of-tree; the committed `evals/` are the durable definitions.
