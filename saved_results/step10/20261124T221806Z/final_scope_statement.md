# Step 10 — Final scope statement

The project will remediate the following failure modes. Step repetition is the highlighted live-agent experiment.

## T1: Step repetition

**Definition(s):** *step_repetition*: Unnecessary reiteration of previously completed steps in a process, potentially causing delays or errors in task completion.

**Pattern:** Chain of Responsibility guard chain (identity, retry budget, state progress) with State-based recovery

**Rationale:** Selected for practical importance and testability, not frequency. Repeated no-progress calls waste cost and can block completion, and a deliberately faulty tool makes the failure reproducible and directly measurable from tool-call logs.

**Supporting evidence:** Model predictions: 4.6% of valid model responses (16.9% including rejected outputs); the gap is explained by the duplicate-quote validator defect found in Step 7. Step 7 disagreement ('List all my notes' / 'List all notes') shows the retry boundary a guard must respect.

**Contrary evidence:** Rare in the human sample (1/17 eligible human traces) and no positive among the 9 team-reviewed GitHub cases. It is not claimed to be the most common failure.

**Uncertainty:** The true predicted rate lies between the valid-only and all-output values. The baseline agent may not repeat naturally; a pilot run checks this first.

**Remediation target:** Detect three consecutive calls with the same normalized tool and arguments and no new information or state progress; route to recovery or an explicit failure; allow retries that make progress.

**Testable claim:** Under a persistent tool fault, the guarded agent produces fewer repetition events than the baseline, without lowering task success under a transient fault.

## T2: Termination lifecycle (missed and premature termination)

**Definition(s):** *unaware_of_termination_conditions*: Lack of recognition or understanding of the criteria that should trigger the termination of the agents’ interaction, potentially leading to unnecessary continuation. *premature_termination*: Ill specified termination condition leading to premature termination Ending a dialogue, interaction or task before all necessary information has been exchanged or objectives have been met. Necessary information constitutes verification of outputs, key data (e.g. api tokens) etc. that are necessary for the success of the task, and agents could have obtained if they tried more or already obtained but failed to communicate to other agents before termination.

**Pattern:** State pattern: Running, Recovering, Completed, Failed

**Rationale:** Both categories are two sides of one missing completion criterion: continuing after the task is done, or stopping before it is done. Both arise when termination is a token or flag instead of an explicit state.

**Supporting evidence:** Human sample: unaware of termination in 4/17 eligible human traces. Model predictions: unaware 3.4% of valid model responses (12.3% including rejected outputs); premature 5.4% of valid model responses (6.9% including rejected outputs). Abstentions concentrate in these two categories, showing implicit completion criteria. GitHub: autogen-6746 carries a TERMINATE state into the next task (design smell).

**Contrary evidence:** Premature termination has 0/4 eligible human traces positive. The team review rejected autogen-7043 because early completion alone does not show an ill-specified condition.

**Uncertainty:** Few eligible human traces for premature termination, and category definitions changed between annotation rounds.

**Remediation target:** Allow the transition to Completed only when task-specific postconditions hold; exhausting the budget moves to Failed with a reason instead of claiming success.

**Testable claim:** In matched scenarios, the State-based controller never reports Completed when postconditions fail and never continues after they hold.

## T3: Missing or incomplete verification

**Definition(s):** *no_or_incomplete_verification*: Lack of critical verification (system designed to but agents didn't) - - robustness (it covers also edge cases) - error handling etc. (broader) Failure to adequately validate or cross-check crucial information or decisions during the iterations, potentially leading to errors or vulnerabilities in the system. 1. verifier exists in the system, but it is weak or badly design 2. the system attempts to verify, but doesn't cover all aspects of the design to make a strong output This is implicitly True if 3.3 Lack of result verification is true, so no longer need to explicitly specify as True.

**Pattern:** Template Method: execute, validate (task-specific hook), decide

**Rationale:** The most frequently predicted category and a direct architectural omission: verification is optional in the observed workflows. A fixed execute-validate-decide skeleton maps cleanly onto Template Method.

**Supporting evidence:** Model predictions: 26.6% of valid model responses (33.8% including rejected outputs), the highest of all categories. Human sample: 3/4 eligible human traces. Largest false-negative group against the upstream AI references (Step 7).

**Contrary evidence:** Only 4 human traces are eligible, so human support is weak. No reviewed GitHub positive: issue reports rarely describe verification.

**Uncertainty:** Predicted rates may partly reflect over-labelling; they are not human-verified prevalence.

**Remediation target:** Make validation a required step before any result is accepted; reject an incorrect artifact with a reason.

**Testable claim:** With a seeded incorrect artifact, the template version rejects it in every matched case where the baseline accepts it, without rejecting correct artifacts.

## Not selected

- **disobey_task_specification:** Strongest human signal (6/18 eligible human traces) and second-highest predicted rate, but a semantic failure that is hard to trigger on purpose and not tied to one structural pattern. Recorded as contrary evidence and a possible extension.
- **fail_to_ask_for_clarification:** 5/18 eligible human traces, but it needs ambiguous multi-agent exchanges and is hard to score objectively.
- **loss_of_conversation_history:** 2 team-reviewed GitHub positives (crewai-8219, crewai-8262) but little trace or model support. Kept as a handoff-contract requirement inside the T1 and T2 prototypes.
- **conversation_reset:** Only 1/17 eligible human traces positive, with no reviewed GitHub or model support.
