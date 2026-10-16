# Gemma paper-track submission content

Author: Jacek Adamek. Unpublished; nothing submitted.

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
No publication, platform Writeup, rule acceptance or submission is authorized.
