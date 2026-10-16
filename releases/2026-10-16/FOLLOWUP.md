# Guided repair follow-up - 16 October 2026

Jacek Adamek, with Codex assistance. This addendum preserves the original submitted paper and separates later experiments from its original claims.

## Original exception-contract finding

The ItsDangerous timestamp repair passed 297 upstream tests but substituted diagnostic text for the original bytes payload. Two feedback attempts did not repair that original failure. The new results below do not change that outcome.

ECA-6 contains six related templated tasks, not six unrelated repositories. All 36 constructed faulty variants passed the weak gate; the first contract gate rejected 35/36. Its six model repairs passed that gate. The post-outcome v2 gate rejected 36/36 mutants and accepted 5/6 model repairs and 6/6 references. The v2 gate is explicitly post hoc. Offline replay covers 102 variants and compares all recorded semantic assertions, rather than only totals.

## Two additional repositories

Tenacity: a falsey callable wait strategy was skipped. The final staged diagnosis and literal-function repair changed both synchronous and asynchronous branches. The tested model patch passed 142 upstream, eight example and nine withheld checks: 159/159.

Packaging: regex match accepted an invalid final newline. Initial, feedback and API-assisted repairs failed some checks, including valid base-name handling. Explicit guidance separated the valid base filename from the named filename branch. The final model function passed 74 upstream, seven example and nine withheld checks: 90/90. A later, post hoc differential comparison with the pinned fixed upstream function found zero differences across 1,245 names. Those names were not a fresh withheld benchmark.

The two final patches pass 249 bounded checks in total. They were reached adaptively after failures, with known localization, public commit descriptions and strong human structural guidance. This is not a first-attempt success rate, a contamination-free benchmark, or evidence of autonomous repository repair. No manual semantic edit was made to the final generated function bodies; the recorded source application rules and preserved surrounding decorators still matter. Tenacity's diagnosis included an unsupported explanation about 0 versus 0.0; passing tests do not validate that explanation.

## Reproduction and licensing

Use REPRODUCE.md and FETCH_UPSTREAM.md for independent local replay. generate_repairs.py records fresh local model outputs separately; a fresh generation is not automatically validated. Model weights, runtime binaries and complete upstream archives are excluded. Pinned revisions, hashes, original prompts, failures and tested patches remain under outputs/. Third-party notices and licenses are preserved; see NOTICE.md. No new competition submission or publication is performed by this package.
