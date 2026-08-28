# Acme Internal Service

## House rules

- All API changes require a review from @platform-team.
- Never commit secrets; load them from the vault at runtime.
- Conventional Commits for every message.

## Deployment notes

We deploy via the internal pipeline; see the runbook in Notion. Do not deploy on Fridays.

Before adding a dependency or running the build, test, or lint toolchain, read the stack reference: @docs/stack.md
