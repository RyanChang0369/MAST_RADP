# Handoff to Steps 11 and 12

Steps 11 and 12 cover exactly these failure modes. Do not add other MAST categories without a team decision.

## T1: Step repetition

- **MAST categories:** step_repetition
- **Live-agent experiment:** yes
- **Baseline mechanism:** The agent retries a failing tool with the same arguments. The error result does not change any control state, and there is no progress check or recovery path, so the loop continues until a hard cap stops it.
- **Intervention to specify:** Detection: three consecutive calls with the same normalized tool and arguments and no new information or state progress. Action: move to recovery (change strategy or escalate) or stop with an explicit failure reason. Outcome: fewer repetition events while retries that make progress are still allowed.
- **Patterns to compare:** Chain of Responsibility, State; alternatives: iteration cap, identical-call counter, retry decorator, circuit breaker.
- **Broken-demo fixture:** Minimal lookup task with a tool that fails persistently; a transient-fault variant; and a normal case where the tool succeeds.
- **Observable failure:** Count of consecutive identical no-progress calls, and the termination reason (cap hit versus task end).
- **Testable claim:** Under a persistent tool fault, the guarded agent produces fewer repetition events than the baseline, without lowering task success under a transient fault.

## T2: Termination lifecycle (missed and premature termination)

- **MAST categories:** unaware_of_termination_conditions, premature_termination
- **Live-agent experiment:** no (deterministic demo only)
- **Baseline mechanism:** Completion is signalled by a keyword, flag or step count instead of checking the task's postconditions. The flag can carry over between runs, so the agent either keeps going after the task is done or stops before the required output exists.
- **Intervention to specify:** Detection: evaluate task-specific postconditions on every step. Action: allow Completed only when they hold; reject further work after Completed; move to Failed with a reason when the budget runs out. Outcome: no false 'completed' and no continuation after completion.
- **Patterns to compare:** State; alternatives: flag or if/else checks, Template Method, Observer.
- **Broken-demo fixture:** Two scenarios with a checkable completion condition: (a) work continues after the condition is met; (b) the run stops before the required output exists; plus a normal case that completes correctly.
- **Observable failure:** Steps executed after the terminal condition held, or a 'completed' status while postconditions fail.
- **Testable claim:** In matched scenarios, the State-based controller never reports Completed when postconditions fail and never continues after they hold.

## T3: Missing or incomplete verification

- **MAST categories:** no_or_incomplete_verification
- **Live-agent experiment:** no (deterministic demo only)
- **Baseline mechanism:** The workflow returns the result straight after execution. Verification is optional or only requested in the prompt, so an incorrect artifact is accepted without any check.
- **Intervention to specify:** Detection: a required, task-specific validation step before any result is accepted. Action: reject an incorrect artifact with a reason. Outcome: incorrect artifacts rejected, correct ones still accepted.
- **Patterns to compare:** Template Method; alternatives: prompt instruction to verify, decorator around tools, Chain of Responsibility for several checks.
- **Broken-demo fixture:** A seeded incorrect artifact (for example a result that fails a known test) and a correct artifact as the normal case.
- **Observable failure:** The incorrect artifact is marked accepted and no validation event appears in the log.
- **Testable claim:** With a seeded incorrect artifact, the template version rejects it in every matched case where the baseline accepts it, without rejecting correct artifacts.

## Not in scope

- disobey_task_specification
- fail_to_ask_for_clarification
- loss_of_conversation_history
- conversation_reset
