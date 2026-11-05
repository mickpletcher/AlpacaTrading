# Dependency consolidation

- Integrate the pending Dependabot updates as a compatible Python 3.13 dependency
  graph and retain immutable CI Action pins.
- Align shared dependency manifests, regenerate the hash lock, and add dependency
  consistency and synthetic compatibility regressions.
- Preserve paper-only execution, existing application boundaries, and protected
  pull-request validation.
