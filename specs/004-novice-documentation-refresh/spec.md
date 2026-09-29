<!-- markdownlint-disable MD013 MD024 MD060 -->

# 004 Novice Documentation Refresh Spec

## Classification

Class 1 documentation change. Runtime behavior, configuration, and interfaces remain unchanged.

## Scope

- Refresh the root overview and beginner setup.
- Refresh the current assessment and tracked defect, debt, and upgrade authorities.
- Correct architecture and component-guide drift.
- Add direct safety warnings around automated paper-order paths.
- Improve validation and operations instructions for first-time users.

## Design

- Use `README.md` as the beginner entry point.
- Keep detailed commands in the existing component guides.
- Use short explanations before commands and state what success looks like.
- Link to authority documents instead of repeating their full content.
- Use `ISSUES.md`, `TECH-DEBT.md`, and `FUTURE-UPGRADES.md` for current tracked work.

## Validation

- Run both documentation compliance commands.
- Run Markdown lint and local Markdown link validation.
- Run `git diff --check`.
- Rerun the repository validation baseline because the current assessment records it.

## Safety

- Documentation must say that live trading is unavailable.
- Automated paper-order guides must identify current blocking defects.
- Example configuration must contain placeholders only.

<!-- markdownlint-enable MD013 MD024 MD060 -->
