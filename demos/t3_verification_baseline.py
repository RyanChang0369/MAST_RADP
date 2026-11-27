import json
import time
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_RESULT = 5
MAX_CALLS = 1
MAX_SECONDS = 2.0


def run_baseline(scenario, produced_result):
    started = time.perf_counter()
    events = []
    calls = 0
    accepted = False
    artifact = None

    if time.perf_counter() - started >= MAX_SECONDS:
        termination_reason = "time_cap_reached"
    elif calls >= MAX_CALLS:
        termination_reason = "call_cap_reached"
    else:
        calls += 1

        # Simulated execution: no API calls or external services.
        artifact = {"result": produced_result}

        events.append({
            "sequence": 1,
            "event": "execution",
            "state": "Running",
            "tool_name": "simulated_addition",
            "normalized_arguments": json.dumps(
                {"a": 2, "b": 3}, sort_keys=True
            ),
            "output": artifact.copy(),
            "error": None,
            "elapsed_seconds": time.perf_counter() - started,
            "termination_reason": None,
        })

        # Deliberate baseline flaw:
        # accept the artifact without invoking a validator.
        accepted = True
        termination_reason = "accepted_without_verification"

        events.append({
            "sequence": 2,
            "event": "acceptance",
            "state": "Completed",
            "tool_name": None,
            "normalized_arguments": None,
            "output": artifact.copy(),
            "error": None,
            "elapsed_seconds": time.perf_counter() - started,
            "termination_reason": termination_reason,
        })

    # Independent experiment measurement AFTER the acceptance decision.
    # This does not influence the baseline's behavior.
    artifact_correct = (
        artifact is not None
        and artifact["result"] == EXPECTED_RESULT
    )

    validation_events = sum(
        event["event"] == "validation"
        for event in events
    )

    return {
        "scenario": scenario,
        "version": "baseline",
        "max_calls": MAX_CALLS,
        "max_seconds": MAX_SECONDS,
        "tool_calls": calls,
        "artifact": artifact,
        "accepted": accepted,
        "artifact_correct": artifact_correct,
        "incorrect_artifact_accepted": accepted and not artifact_correct,
        "validation_events": validation_events,
        "termination_reason": termination_reason,
        "events": events,
    }


def main():
    runs = [
        run_baseline("incorrect_artifact", produced_result=6),
        run_baseline("correct_artifact", produced_result=5),
    ]

    incorrect, correct = runs

    assert incorrect["incorrect_artifact_accepted"]
    assert incorrect["validation_events"] == 0

    assert correct["accepted"]
    assert correct["artifact_correct"]
    assert correct["validation_events"] == 0

    output_folder = Path(__file__).resolve().parent / "results"
    output_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_path = output_folder / f"t3_baseline_{timestamp}.json"
    output_path.write_text(
        json.dumps(runs, indent=2),
        encoding="utf-8",
    )

    for run in runs:
        print(
            f"{run['scenario']}: "
            f"accepted={run['accepted']}, "
            f"correct={run['artifact_correct']}, "
            f"validation_events={run['validation_events']}"
        )

    print(f"\nLogs saved to: {output_path}")


if __name__ == "__main__":
    main()