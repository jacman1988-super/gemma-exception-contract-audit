# ImportGuard — local research prototype for the Gemma Paper Track

Author: Jacek Adamek.

Status: original implementation and controlled fixtures, unpublished, not submitted.
AI coding assistance: Codex. Actual local Gemma 4 E2B inference is recorded in
local-model-pilot.txt. No competition-provided data was used for this project.

Question: can explicit fallback for uncertain Python imports reduce missed regression
tests when a coding agent has a limited test budget? The tool computes reverse import
reachability from changed modules and falls back to all tests for recognized uncertainty.
It emits source hashes so a selection can be tied to the exact source snapshot.

Python 3.12, no third-party dependencies:

```sh
python -m unittest -v
python benchmark.py
python importguard.py /path/to/repository src/changed.py
```

The benchmark actually executes clean and mutated code in temporary directories. Its
four constructed cases cover direct, transitive, relative and dynamic imports. A fixed
one-file prefix is an intentionally weak budget control, not a competitive baseline.
Timings include process startup and should not be interpreted as speedup evidence.

This is module-level selection, not a sound analyser. Indirect dynamic imports, runtime
plugins, reflection, implicit resource dependencies and monkeypatching remain limitations.
Always run the full suite before release. The original benchmark executes only generated fixtures; the separate upstream
pilot executes reviewed public test subsets. Use a suitable sandbox for external code.

New executed stress experiment: see stress-experiment.txt and the raw JSONs in
results/stress-baseline-v1.json and results/stress-alias-fix-v2.json. The initial
selector found 6/8 controlled faults using 23 test modules; alias handling now
finds 8/8 using 33 versus 48 for the full suite. These cases informed the fix,
so the corrected result is regression evidence, not an independent assessment.
Nine selector tests pass. Original snapshots and negative results are retained.

```sh
python stress_benchmark.py --selector v1 --output results/stress-baseline-v1.json
python stress_benchmark.py --output results/stress-alias-fix-v2.json
```

Before a research submission: review regression-test-selection literature, freeze
independent real bug/fix pairs and run actual Gemma agents with model, version,
hardware and inference budget recorded. Include coverage setup cost and repository
clustered uncertainty. Novelty and competitiveness remain unestablished.
See research-plan.txt and related-work-notes.txt.

Contest: https://www.kaggle.com/competitions/gemma-4-developer-agent-paper
Network access is limited to explicit public snapshot downloads in fetch_pilot.py.
No account mutation, payment, registration or submission code is included.

Executed upstream pilot (real-bugs-pilot.txt): two pinned public fixes, fixed
references of 74 and 768 passing tests, and reproduced parent-code failures.
Fallback selected all five declared modules: no selection saving. These are
convenience development cases, not independent held-out repositories.

Actual local Gemma pilot (local-model-pilot.txt): two one-shot suggestions,
one unresolved bug and one patch passing all 768 declared tests. This is not
an iterative agent study. Raw outputs, failed restricted-launch attempts,
source licenses and a protocol hash audit are included. Do not infer scientific
novelty, a leaderboard result, or a general success rate from two tasks.

The upstream pilot additionally requires requirements-pilot.txt (pytest 8.4.2).
Use fetch_pilot.py for verified public snapshots, real_bug_benchmark.py for the
selector pilot, and local_model_pilot.py with separately downloaded official
model/runtime files for inference. See THIRD-PARTY-NOTICES.txt.

One-retry controlled pilot: results/feedback-pilot/ records a predeclared
no-feedback review and a test-feedback review of the same failed boltons edit.
Both generated the identical passing function. One actual 74-test run is shared
for the identical patch. This case provides no evidence of additional benefit
from test feedback. Both the successful control and that limitation are retained.

paper-draft.txt is an English working paper below 3000 words, not a submission
or a novelty claim. pipeline.ipynb documents reproduction; its cells have not
been executed as a notebook. The script results are the executed evidence.
feedback_pilot.py records new text only. evaluate_feedback_pilot.py accepts only
the exact function reviewed for this experiment; arbitrary model output is refused.

Frozen expansion (expansion-study.txt) retains all five selected new cases:
three primary reproductions, one failed Windows-encoding reference and one
uninformative test pool. A separate UTF-8 follow-up reproduces the encoding case.
The frozen selector offers no saving on the reproduced cases. Three primary
Gemma proposals fail; the secondary proposal is a no-op. No retry or manual
repair replaces these outcomes. Exact protocols and licenses are in results/.
The initial paper and notebook stage remain as historical records; current
paper-draft.txt includes the expansion and remains below 3000 words.

Separate development variant: importguard_layout.py supports explicit source
roots (--source-root src), preserves fallback and detects ambiguous names.
Seven new tests plus nine frozen-selector tests pass. layout-correction.txt and
results/layout-regression/ document a post-outcome regression check, not a fresh
assessment. The frozen importguard.py and negative model results are unchanged.

Discovery regression: `importguard_discovery.py` repairs suffix/bare-prefix discovery without changing frozen variants. `discovery_benchmark.py` records 2/4 old versus 4/4 new mutation detections in deliberately constructed fixtures; no new model inference or independent generalization claim. All 19 tests pass. Raw logs: `results/discovery-regression/`.

Further known-upstream verification: results/upstream-discovery-review/. Four reproduced faults detected, one uninformative case retained; full declared pools selected throughout, no saving. Not a new holdout or model run.

New repositories: new_repository_benchmark.py, results/new-repositories/ and separate freezegun dependency follow-up. ItsDangerous: fixed 101 pass, parent 1 fail/100 pass; SortedContainers: both 59 pass (uninformative, retained). One of two cases reproduced; no selected-module savings. No new model inference. Reproduction requires requirements-new-repositories.txt, fetch_new_repositories.py, and an unused output directory.

2026-10-15 actual model trial: results/itsdangerous-model*/. 256-token truncation retained; identical-prompt 1024-token patch passes 297 tests but changes exception payload bytes to str. A separate feedback-informed 512-token proposal still fails the original test. No fully contract-preserving repair established; all failures retained. No manual patch corrections.

Further localized feedback trial: results/itsdangerous-model-localized-feedback/. Model again edits the wrong handler: 1 failed / 296 passed. Three added post-outcome contract probes: reference 3 pass, model 1 fail / 2 pass. No complete repair established; all attempts retained.
