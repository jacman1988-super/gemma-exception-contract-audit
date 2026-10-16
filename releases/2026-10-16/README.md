# Exception-contract audit and guided Gemma repairs

Author: **Jacek Adamek**. Prepared source release: **2026.10.16**.

This is a reproducible audit artifact, not an autonomous coding-agent benchmark. It preserves the original ItsDangerous counterexample and ECA-6 resource, plus clearly separated follow-ups on Tenacity and Packaging. Prepared for `jacman1988-super/gemma-exception-contract-audit`; nothing here publishes or changes the submitted Kaggle writeup.

## What the evidence shows

- An ItsDangerous model repair passed 297 upstream tests while changing exception payload metadata. **That counterexample has not been repaired by the newer follow-ups.**
- ECA-6 contains six related, templated diagnostic tasks and 36 constructed faulty patches. All six model outputs passed the initially frozen checks. A separately labeled post-outcome audit found a message regression: five passed the strengthened gate. That gate rejected all 36 calibration faults.
- Guided follow-ups now have test-passing repairs for two different public repositories:

| Case | Upstream module | Example controls | Withheld controls | Total |
|---|---:|---:|---:|---:|
| Tenacity | 142/142 | 8/8 | 9/9 | **159/159** |
| Packaging | 74/74 | 7/7 | 9/9 | **90/90** |

Packaging also agrees with the pinned upstream function on **1,245 post-hoc filename cases**. These are extra robustness checks, not an independent hidden benchmark. All earlier failures remain in the archive.

**Assistance matters:** Tenacity used a separate model diagnosis followed by literal-function output. Packaging needed further explicit human decomposition into two filename families and requested branches, after earlier example/API feedback failed. This is not a first-attempt 2/2 success rate, not evidence that all Gemma repairs are correct, and not an extension of ECA-6 with two independent exception-contract tasks.

## Start here

```text
python -m pip install -r requirements.txt
python verify_release.py
python -m pytest -q
python reproduce.py /ABSOLUTE/NEW_ECA_OUTPUT
```

`reproduce.py` recomputes all 102 recorded ECA-6 case/variant evaluations without a model and compares every case/assertion outcome. Outputs must go into a new directory.

To replay the reviewed public-repository repairs with separately obtained pinned archives:

```text
python replay_repairs.py --archives PINNED_ARCHIVE_DIRECTORY --output /ABSOLUTE/NEW_REPLAY_OUTPUT
```

See [REPRODUCE.md](REPRODUCE.md), [REPORT.pdf](REPORT.pdf) and [FETCH_UPSTREAM.md](FETCH_UPSTREAM.md). Local tested patches are `outputs/gemma-feedback-v4/tenacity-tested.patch` and `outputs/gemma-branch-feedback-v5/packaging-tested.patch`.

## Provenance and distribution

Original code is Apache-2.0; third-party snippets retain their upstream licenses. Model weights, runtime binaries, full upstream repositories and account administration are not distributed. Model prompts and raw outputs are retained. Historical manifests/readiness fields describe earlier runs; `RELEASE_MANIFEST.json` describes this prepared source package.

The original submitted paper is archived unchanged at `outputs/gemma-importguard/submission-paper.pdf`. [FOLLOWUP.md](FOLLOWUP.md) and the new report describe the later guided experiments; they do not replace or silently revise that paper. See [NOTICE.md](NOTICE.md).
