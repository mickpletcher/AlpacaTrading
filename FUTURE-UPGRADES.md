<!-- markdownlint-disable MD013 MD024 MD060 -->

# Future Upgrades

FU-001 was completed as the paper-only execution boundary recorded under Upgrade 004 in `upgrades/README.md`. Live trading remains unavailable and would require a new Class 4 proposal.

## FU-002: Reproducible strategy evaluation pipeline

**Status:** Proposed
**Priority:** Medium
**Area:** Backtesting
**Origin:** Internal

**Opportunity:** Standardize datasets, transaction costs, benchmark metrics, out-of-sample periods, and walk-forward reports.

**Potential benefit:** Comparable evidence across strategies and fewer misleading historical results.

**Why deferred:** Current repository work is focused on correctness and safety.

**Trigger:** Before promoting a strategy beyond paper experimentation.

**Estimated effort:** Large

**Dependencies:** TD-006

## FU-003: Operational status and alerting

**Status:** Proposed
**Priority:** Medium
**Area:** Operations
**Origin:** Internal

**Opportunity:** Add a local status view for scheduler runs, bot health, circuit-breaker state, rejected orders, and stale data.

**Potential benefit:** Faster detection of silent failures during unattended paper runs.

**Why deferred:** Central monitoring is not required for local paper experiments.

**Trigger:** When one bot is approved for unattended paper operation.

**Estimated effort:** Medium

**Dependencies:** None

<!-- markdownlint-enable MD013 MD024 MD060 -->
