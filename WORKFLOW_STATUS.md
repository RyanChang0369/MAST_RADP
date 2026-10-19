# Consolidated workflow and Step 6 status

## How to use the notebook

Close the old notebook tab without overwriting the updated disk file. Reopen llm_judge_pipeline.ipynb, choose the project .venv kernel, restart the kernel, and use Run All. All API flags are False. The module also denies evaluation calls unless explicitly enabled; a fresh kernel resets that switch. Run All is an offline preparation and saved-results review, not a new evaluation run.

## One active workflow file

`gemini_workflow.py` is the only active root workflow file. Explicit modes: `four_category`, `fourteen_category`, `full_v1`, `evidence_v2`, `evidence_v2_recovery`. Example: `workflows.get_mode("evidence_v2")`. The current evidence-v2 prompt and validation remain unchanged. Recovery mode preserves invalid responses and never retries them automatically.

The frozen implementation bodies are embedded verbatim in separate mode namespaces rather than aggressively deduplicated, so category/prompt differences cannot leak between experiments. Immutable originals are archived as historical checksum witnesses. Do not delete the consolidation archive: frozen loaders verify it. This is a maintenance consolidation, not a claim of faster API inference or lower quota usage.

## Verified offline

- 20 regression tests passed, including the original evidence tests and API-disabled checks for all modes.
- All 19 notebook code cells executed successfully in order with socket connections blocked.
- Original saved result bytes and freeze-manifest bytes were unchanged.
- Original implementation hashes match their archived witnesses. Superseded root modules were removed only after offline checks passed; tests also passed after removal.
- Combined pilot audit verifies prompt fidelity, duplicate attempts, raw response parsing, and strict exact-quote validation.

## Pilot results

14 selected / 14 attempted / 10 valid / 4 invalid / 0 unattempted. Valid trace-response coverage: 71.4%. Invalid responses remain unavailable, not negative. Three failed exact-substring validation and one failed duplicate-quote validation.

Aggregate category-reference counts (AI references, NOT human accuracy):

```json
{
  "eligible": 196,
  "valid_responses": 140,
  "unavailable": 56,
  "abstentions": 2,
  "scored": 138,
  "tp": 5,
  "tn": 110,
  "fp": 4,
  "fn": 19
}
```

Per-category agreement, precision, recall, F1, abstentions, response coverage and decision coverage are in `data/processed/step6_consolidated_audit/pilot_audit.json` and notebook Step 6C.14. Invalid responses are excluded from binary confusion counts but included in unavailable/coverage counts. The recovery executor differs, so run provenance is retained instead of presenting the three folders as a single uninterrupted frozen execution.

## Step 6 is still open

1. Semantic review of the valid judgments and false-negative/abstention risks: quote existence is not semantic correctness. The previous review covered four full short traces plus targeted checks of ten long traces, not a full independent validation.
2. Independent teammate/human taxonomy and evidence review: not recorded and cannot be supplied by this automated refactor.
3. The old technical pilot request marked generation_started has no saved response. Its upstream outcome remains unknown; preserve its record and lock. Do not retry automatically. No provider reconciliation was attempted because API calls were prohibited.
4. Final approved evaluation configuration and explicit authorization/quota scope for full development and held-out evaluation. Those corpus partitions have not been fully evaluated. Do not tune on held-out outcomes.

No sign-off or clinical/production/model-quality claim is implied by passing these software checks. No new model requests were made during consolidation.

## Portable teammate setup

The first code cell now calls setup_project. Share llm_judge_pipeline.ipynb and gemini_workflow.py together. A fresh project downloads only the two public datasets at the pinned revision (~202 MB total), verifies SHA-256 checksums, restores embedded frozen manifests and historical checksum witnesses, and prepares the human source records. Published NaN annotation votes are normalized to missing values (None), not assigned labels. No pip packages or Gemini key are required for the offline notebook path; a working Python kernel is required. Internet is needed only when datasets are absent. DOWNLOAD_DATASETS=True controls public downloads only. Keep every RUN_* flag False.

Tested all 20 code cells on the existing project with networking blocked and in a clean two-file project simulation with mocked public download streams. Both pinned public URLs returned HTTP 200 on HEAD checks; a fresh full live download was not repeated. No Gemini calls were made. Missing saved_results folders produce a no-results-local summary, not recreated results. Historical checksum witnesses can now be restored by setup; they no longer need to be copied separately.

## Latest evidence-v3 development result

Evidence-v3 was added inside the same consolidated file after scoped semantic review. All 14 development cases have now been attempted: 12 valid responses, one quote-validation failure, one request failure without a saved response, zero unattempted. The eight-case continuation excluded all six prior attempts and made no retries. Some semantic concerns remain and are documented in data/processed/step6_consolidated_audit/HUMAN_REVIEW_V3.md. Human reviewer: Husna (nominated, not approved). Full development and held-out runs are still off. See notebook Step 6C.16 for combined metrics. The latest offline Run All passed 22 code cells; 21 tests passed. No new Gemini calls were made in those checks.

## Scope correction and live broad evaluation

Original user-provided Step 6: build and pilot an LLM-based classifier on a sample, with traceable saved outputs, visible technical failures and parser tests. That implementation deliverable is complete with documented limitations. A separate teammate review is part of Step 16 pattern-choice review and must not be imposed as a new Step 6 gate. The user additionally requested broad dataset coverage; that extension has now been started using Gemini in bounded development batches.

Read data/processed/step6_consolidated_audit/full_evaluation_status.json or notebook Step 6C.17 for actual progress; never assume the entire corpus finished from a started process. Caps: 20 generation requests and 1,000,000 counted input tokens per batch, existing local request limits, no billing changes, no automatic generation retries. Stop on provider/transport errors or daily quota cap. Heldout stays untouched until development attempts are accounted for. The exact frozen v3 prompt remains unchanged throughout. The latest runner tests passed 27/27 in the project .venv.

## Eight-requirement notebook and provider stop

The active notebook has been reorganized to match the eight original Step 6 requirements; the former seventeen extension/recovery milestones are archived. See STEP6_CHECKLIST.md. All nine current code cells passed offline. The broader worker stopped on Gemini HTTP 503, preserving the failed request without retry: 65 valid, 19 invalid_response, 2 earlier error, 1 request_error, 1 generation_started and 1 blocked development records; 1,125 development and all 323 held-out traces remain unattempted at the stop checkpoint. No classifier prompt/schema changes were made during held-out evaluation; no held-out request has occurred. Section 8 displays direct current-record coverage. Human manual sign-off is not fabricated.

## Latest Steps 1–6 cleanup

The active notebook now follows the actual project Steps 1–6; the eight classifier requirements are nested as 6.1–6.8. The public-data setup remains the first code cell. Historical experiments and outputs are archived. All 14 code cells passed offline and 29 tests passed in .venv. Current live control: section 6.8, RUN_NEW_GEMINI_BATCH (default False). The post-batch summary now reads current files AFTER execution, suppresses per-trace log clutter, and shows the latest manual-batch error instead of an old supervisor checkpoint. No new Gemini requests were made during cleanup. No frozen classifier prompt/schema, source dataset, or saved model result was changed.

The most recent user-launched batch stopped at Gemini HTTP 503 after 16 generation attempts: 11 valid, 4 invalid, 1 request error. This is a provider interruption, not repaired by UI cleanup. Current overall development counts: 76 valid, 23 invalid_response, 2 earlier error, 2 request_error, 1 generation_started and 1 blocked; 1,109 development and all 323 held-out traces remain unattempted. No background run is active. Failed/invalid/unknown traces remain excluded from automatic retries.
