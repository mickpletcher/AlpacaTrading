# Generate Plan For Trading Repo

Create an execution plan for the target spec package in this repository.

## Planning Rules

1. Build from the approved `requirements.md` and `spec.md`.
2. Prefer additive changes over destructive changes.
3. Group work by coherent implementation slices.
4. Identify exact files and folders likely to change.
5. Include verification steps after each major slice.
6. Separate stable retrofit work from follow-up debt that should not be folded into the same change.

## Required Considerations

- Python dependency changes in `requirements.txt`
- PowerShell module compatibility in `src/`
- `Tests/` updates or gaps
- README and docs updates
- CI workflow impact

## Output Format

Write `specs/<NNN-name>/plan.md` with:

- objective
- assumptions
- ordered phases
- per-phase file touch list
- validation steps
- rollback or safety notes when applicable
