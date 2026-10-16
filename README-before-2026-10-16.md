# Gemma paper-track submission content

Author: Jacek Adamek. Public research archive; no competition submission has been made.

Current paper: **Beyond 297 Passing Tests: Auditing Exception Contracts in Local Gemma Repairs**.
Start with GOTOWE-DO-ZGLOSZENIA.txt. The prepared Writeup is submission-writeup.txt;
submission-paper.pdf is the optional PDF. submission-fields.json lists platform fields.

The contribution is an executable ECA-6 diagnostic resource and a bounded local-model
case study. It does not claim a complete model repair, safe test selection, general
error rates or a novel differential-testing algorithm. Both positive and negative
findings are retained. Six constructed tasks are correlated. V2 is post-outcome.

Run `python verify_submission.py` for current submission-content checks.
Run `python -m pytest -q` for implementation tests.
Run `python reproduce_contract_resource.py FRESH_DESTINATION` to recompute resource
test outcomes without model weights (Python 3.12, pytest 8.4.2).
Read ECA-6-DATASHEET.txt for protocols, inference requirements and limitations.

submission-review.ipynb reads the recorded results; submission-review-executed.ipynb
contains actual plain-CPython cell execution, explicitly not a Jupyter-kernel claim.
The complete resource outputs are in results/exception-contract-resource/.

Earlier paper/source files and verify_final.py preserve prior project stages.
Their historical readiness comments describe earlier scope, not this prepared paper.
Scientific merit and individual eligibility are not guaranteed by local checks.
The owner authorized this code/report publication. No platform Writeup, new rule acceptance or competition submission is authorized.

## Publication scope

This public release was explicitly authorized by the participant. Historical JSON files and local-review documents preserve their original dated publication/submission status; those snapshots do not describe the current visibility of this repository. No Kaggle entry or organizer-form submission is performed by publishing this archive.

The current paper is submission-writeup.txt; the optional PDF is submission-paper.pdf. ECA-6 is a small constructed diagnostic resource with post-outcome v2 checks, not an independent generalization benchmark. Model failures and semantic regressions are retained.

## Complete reproducible release

The root contains readable code, notebooks and reports. **Before running the pipeline or verifiers, run `python unpack_release.py` once.** This validates and expands the bundled `source-and-results.zip` into this checkout, adding every results subdirectory, frozen model/configuration, reference excerpt and historical record. The archive is part of this repository; no additional unpublished file is needed. Input images for Solar and optional Gemma weights remain separately acquired resources as documented. The archive contains no credentials, full input dataset or model weights.

Then install the pinned project requirements in your own Python environment and follow the existing reproduction instructions. Publication is not a Kaggle or organizer-form submission. Dated publication flags inside experimental snapshots are historical records.
