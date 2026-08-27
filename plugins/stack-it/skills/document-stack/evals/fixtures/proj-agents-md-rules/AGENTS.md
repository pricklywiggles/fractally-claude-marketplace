# Contributor and agent rules

## Code style

- Function components only. No class components anywhere in `src/`.
- Co-locate a component's test next to it as `<Component>.test.tsx`.
- Imports are sorted by the linter; never hand-sort them.

## Review

- Anything touching `src/api/` needs a second reviewer.
- Never commit a `.env` file. Secrets come from the deploy environment.

Before adding a dependency or running the build, test, or lint toolchain, read the stack reference: @docs/stack.md
