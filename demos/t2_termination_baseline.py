import json
import time
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_OUTPUT = ["A", "B", "C"]
MAX_CALLS = 6
MAX_SECONDS = 2.0


def run_baseline(scenario, initial_completed_flag=False):
    started = time.perf_counter()
    artifact = []
    events = []
    calls = 0
    steps_after_completion = 0
    completed_flag = initial_completed_flag
    termination_reason = None

    def postconditions_hold():
        return artifact == EXPECTED_OUTPUT

    # Deliberately flawed baseline:
    # the completion flag controls execution.
    # Postconditions are measured for the experiment but do not control it.
    while True:
        if completed_flag:
            termination_reason = "completion_flag"
            break

        if time.perf_counter() - started >= MAX_SECONDS:
            termination_reason = "time_cap_reached"
            break

        if calls >= MAX_CALLS:
            termination_reason = "call_cap_reached"
            break

        complete_before_step = postconditions_hold()
        if complete_before_step:
            steps_after_completion += 1

        calls += 1

        if len(artifact) < len(EXPECTED_OUTPUT):
            artifact.append(EXPECTED_OUTPUT[len(artifact)])
            output = {"action": "append", "artifact": artifact.copy()}
        else:
            output = {"action": "unnecessary_work", "artifact": artifact.copy()}

        if scenario == "normal":
            completed_flag = calls >= 3
        elif scenario == "premature_termination":
            completed_flag = calls >= 1
        elif scenario == "missed_termination":
            completed_flag = False
        elif scenario == "stale_flag":
            # A previous run's flag was incorrectly reused.
            pass
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

        events.append({
            "sequence": len(events) + 1,
            "event": "tool_result",
            "state": "Running",
            "call_number": calls,
            "tool_name": "artifact_builder",
            "normalized_arguments": json.dumps(
                {"target": EXPECTED_OUTPUT}, sort_keys=True
            ),
            "output": output,
            "error": None,
            "postconditions_before": complete_before_step,
            "postconditions_after": postconditions_hold(),
            "completion_flag": completed_flag,
            "elapsed_seconds": time.perf_counter() - started,
            "termination_reason": None,
        })

    reported_status = "Completed" if completed_flag else "Failed"
    output_correct = postconditions_hold()
    false_completed = reported_status == "Completed" and not output_correct

    events.append({
        "sequence": len(events) + 1,
        "event": "termination",
        "state": reported_status,
        "call_number": calls,
        "tool_name": None,
        "normalized_arguments": None,
        "output": artifact.copy(),
        "error": None,
        "postconditions_after": output_correct,
        "completion_flag": completed_flag,
        "elapsed_seconds": time.perf_counter() - started,
        "termination_reason": termination_reason,
    })

    return {
        "scenario": scenario,
        "version": "baseline",
        "max_calls": MAX_CALLS,
        "max_seconds": MAX_SECONDS,
        "initial_completed_flag": initial_completed_flag,
        "artifact": artifact,
        "tool_calls": calls,
        "output_correct": output_correct,
        "reported_status": reported_status,
        "false_completed": false_completed,
        "steps_after_completion": steps_after_completion,
        "termination_reason": termination_reason,
        "events": events,
    }


def main():
    runs = [
        run_baseline("normal"),
        run_baseline("premature_termination"),
        run_baseline("missed_termination"),
        run_baseline("stale_flag", initial_completed_flag=True),
    ]

    normal, premature, missed, stale = runs

    assert normal["output_correct"]
    assert normal["reported_status"] == "Completed"
    assert normal["steps_after_completion"] == 0

    assert premature["false_completed"]
    assert premature["artifact"] == ["A"]

    assert missed["output_correct"]
    assert missed["steps_after_completion"] == 3
    assert missed["termination_reason"] == "call_cap_reached"

    assert stale["false_completed"]
    assert stale["tool_calls"] == 0

    output_folder = Path(__file__).resolve().parent / "results"
    output_folder.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_path = output_folder / f"t2_baseline_{timestamp}.json"
    output_path.write_text(
        json.dumps(runs, indent=2),
        encoding="utf-8",
    )

    for run in runs:
        print(
            f"{run['scenario']}: "
            f"calls={run['tool_calls']}, "
            f"status={run['reported_status']}, "
            f"false_completed={run['false_completed']}, "
            f"extra_steps={run['steps_after_completion']}"
        )

    print(f"\nLogs saved to: {output_path}")


if __name__ == "__main__":
    main()