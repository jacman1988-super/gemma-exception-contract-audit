# Reproduction

Python 3.12. Install `requirements.txt`, then run the root offline checks. Neither root command accepts contest rules, sends requests to a competition, publishes a repository or buys inference.

## ECA-6: 102 frozen evaluations without model inference

```text
python reproduce.py /ABSOLUTE/NEW_OUTPUT
```

The output directory must not exist. This runs 42 initial calibration variants, six initial model variants and 54 strengthened-audit variants. It compares individual outcomes and assertions, not just aggregate totals. The original weak/contract-v1 and post-outcome v2 stages remain separate. The reference result is preserved in `outputs/gemma-importguard/results/exception-contract-resource/`.

## Tenacity and Packaging: fixed, parent and reviewed model variants

Obtain the four pinned archives listed in `FETCH_UPSTREAM.md`. They are not bundled. Then:

```text
python replay_repairs.py --archives /ARCHIVE_DIRECTORY --output /ABSOLUTE/NEW_OUTPUT
```

The script verifies archive SHA256, refuses path traversal, skips symbolic links, verifies fixed test-file hashes and creates isolated source copies. It applies only stored, reviewed literal functions whose generation hashes match. Original decorators remain outside the replacement spans. It checks complete JUnit counts/identities and requires fixed and model variants to pass, while parent upstream modules must fail. It preserves logs and does not touch published evidence. Tests include local asyncio; environments that block local event-loop/process execution cannot reproduce that subset until those local restrictions are removed.

## Fresh local model generations

```text
python generate_repairs.py --plan
python generate_repairs.py --model LOCAL_MODEL.gguf --executable LOCAL_LLAMA_CLI --output /ABSOLUTE/NEW_OUTPUT
```

Use the recorded model SHA256 and llama.cpp b11429 / d81235049. The plan shows all frozen prompt hashes without loading a model. The Tenacity repair prompt includes its recorded diagnostic response; Packaging uses the final strongly guided branch prompt. This replays the final assisted prompts, not a new unassisted trial or the entire adaptive history. Fresh output is text only and is never executed automatically.

The original two-stage and subsequent failed feedback attempts remain under `outputs/gemma-feedback-v3/`, `gemma-feedback-v4/` and `gemma-branch-feedback-v5/`. Individual protocols define their budgets, assistance and exclusions. No generated edit was manually corrected and then credited to the model.
