# Gemma: proposed Writeup update and public supporting materials

Author: Jacek Adamek. Prepared 16 October 2026. No competition update has been submitted.

- [Complete proposed Writeup](writeup-update.txt): 2369 words including title/author/references, below the 3000-word maximum.
- [PDF paper](paper-update.pdf): publicly readable optional supporting paper.
- [Review notebook](review-update.ipynb) and [executed review](review-update-executed.ipynb).
- [Change summary](change-summary.txt) separates new guided cases from the original ECA-6 and ItsDangerous findings.
- [Recorded public-copy verification](PUBLIC-REPRODUCTION.json).

The final guided Tenacity and Packaging patches pass 159/159 and 90/90 checks. They followed earlier failures and explicit assistance. The original ItsDangerous failure remains unresolved. This is not a first-attempt repair success rate or independent generalization evidence.

From the repository root, with Python 3.12:

```text
python -m pip install -r submission-update-2026-10-16/requirements.txt
python submission-update-2026-10-16/verify_materials.py
python releases/2026-10-16/verify_release.py
python -m pytest releases/2026-10-16/tests -q
python releases/2026-10-16/reproduce.py NEW_ECA_OUTPUT
```

The review notebook can run from this directory or the repository root. It reads frozen evidence and checks prompt digests; it does not execute model-generated repairs. For complete repair replay, follow the older release's REPRODUCE.md and FETCH_UPSTREAM.md (four public hash-pinned archives). For optional fresh generation, the model weights/runtime must be separately obtained from their official sources, as described in that release. No proprietary account or paid inference service is required for the published outcome replay. Model weights and upstream archives are not republished here.

The executed notebook records explicit plain CPython execution of its three code cells; it does not claim a Jupyter-server execution. Use your existing Jupyter frontend if desired. PDF generation used ReportLab 4.4.9; requirements-docs.txt lists optional document tooling. Proposed paper text is CC BY 4.0 in line with the accepted Writeup terms; original tooling remains Apache-2.0, and upstream notices remain unchanged. The original submitted paper stays at the repository root. On future authorization, update the existing Kaggle Writeup rather than creating a duplicate entry.

## Execute the notebook without a Jupyter installation

The public run_notebook.py executes only the notebook supplied in this directory using plain CPython. Use a new output path:

```text
python submission-update-2026-10-16/run_notebook.py --output work/executed-gemma.ipynb
```

This review reads and checks frozen evidence. Follow the separate release commands above for ECA and repaired-upstream replay.
