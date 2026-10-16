# Exception-contract audit and guided Gemma repairs

Author: **Jacek Adamek**.

## Complete competition-update materials

Start with [submission-update-2026-10-16/README.md](submission-update-2026-10-16/README.md) for the latest notebook, exact commands, integrity checks and proposed competition-update documents.


Author: **Jacek Adamek**. Latest research update: **16 October 2026**.

The new release preserves the original ItsDangerous counterexample and ECA-6 resource, adding separately documented guided repair case studies in Tenacity and Packaging. The final reviewed patches pass **159/159** and **90/90** bounded tests. Packaging also agrees with the pinned fixed function on 1,245 post-hoc filename cases.

The repairs followed earlier failures and explicit assistance, including human structural guidance for Packaging. This is not an unassisted first-attempt success rate. **The original ItsDangerous exception-payload failure remains unresolved.** The unchanged original submitted paper remains at [submission-paper.pdf](submission-paper.pdf); the later findings are a separate [follow-up](releases/2026-10-16/FOLLOWUP.md).

Release checks: **25 tests passed**; all **102 ECA variants** and the two reviewed repository repairs were reproduced from the prepared release.

## Reproduce this update

See [release README](releases/2026-10-16/README.md), [reproduction instructions](releases/2026-10-16/REPRODUCE.md), [research report](releases/2026-10-16/REPORT.pdf) and [validation record](releases/2026-10-16/VALIDATION.json).

Run the documented commands from `releases/2026-10-16/`. The dated release includes its own file manifest and offline integrity verifier. Its preparation records describe the local checks performed before this GitHub update. Full training and fresh model generations were not repeated during packaging.

## Earlier version

The [previous README](README-before-2026-10-16.md), original root code and original reports remain available. This GitHub update does not submit or modify a competition entry. Competition inputs, trained weights and new prediction CSVs are not included in the update.
