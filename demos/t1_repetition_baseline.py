import json
import time
from datetime import datetime, timezone
from pathlib import Path

MAX_CALLS = 6
MAX_SECONDS = 2.0


def run_baseline(scenario, failures_before_success):
    """None means the simulated tool fails persistently."""
    started = time.perf_counter()
    events = []
    calls = 0
    consecutive_no_progress = 0
    longest_no_progress = 0
    result = None
    termination_reason = None

    arguments = {"query": "project_deadline"}
    normalized_arguments = json.dumps(arguments, sort_keys=True)

    while True:
        elapsed = time.perf_counter() - started

        if elapsed >= MAX_SECONDS:
            termination_reason = "time_cap_reached"
            break

        if calls >= MAX_CALLS:
            termination_reason = "call_cap_reached"
            break

        calls += 1

        # Local simulated tool: no network or API calls.
        tool_fails = (
            failures_before_success is None
            or calls <= failures_before_success
        )

        if tool_fails:
            output = None
            error = "lookup_unavailable"
            consecutive_no_progress += 1
            longest_no_progress = max(
                longest_no_progress, consecutive_no_progress
            )
        else:
            output = {"project_deadline": "Friday"}
            error = None
            consecutive_no_progress = 0

        events.append({
            "sequence": len(events) + 1,
            "event": "tool_result",
            "state": "Running",
            "call_number": calls,
            "tool_name": "primary_lookup",
            "normalized_arguments": normalized_arguments,
            "output": output,
            "error": error,
            "made_progress": not tool_fails,
            "consecutive_identical_no_progress": consecutive_no_progress,
            "elapsed_seconds": time.perf_counter() - started,
            "termination_reason": None,
        })

        if not tool_fails:
            result = output
            termination_reason = "task_completed"
            break

        # Baseline behavior: retry the same call after every failure.

    task_success = result == {"project_deadline": "Friday"}
    final_state = "Completed" if task_success else "Failed"

    events.append({
        "sequence": len(events) + 1,
        "event": "termination",
        "state": final_state,
        "call_number": calls,
        "tool_name": None,
        "normalized_arguments": None,
        "output": result,
        "error": None,
        "made_progress": False,
        "consecutive_identical_no_progress": consecutive_no_progress,
        "elapsed_seconds": time.perf_counter() - started,
        "termination_reason": termination_reason,
    })

    return {
        "scenario": scenario,
        "version": "baseline",
        "max_calls": MAX_CALLS,
        "max_seconds": MAX_SECONDS,
        "failures_before_success": failures_before_success,
        "tool_calls": calls,
        "longest_identical_no_progress_streak": longest_no_progress,
        "repetition_threshold_reached": longest_no_progress >= 3,
        "calls_after_three_no_progress": sum(
            event["event"] == "tool_result"
            and event["call_number"] > 3
            for event in events
        ),
        "task_success": task_success,
        "final_state": final_state,
        "termination_reason": termination_reason,
        "events": events,
    }


def main():
    scenarios = [
        ("normal", 0),
        ("transient_fault", 2),
        ("persistent_fault", None),
    ]

    runs = [
        run_baseline(name, failures)
        for name, failures in scenarios
    ]

    # Check that the fixtures demonstrate the intended behavior.
    normal, transient, persistent = runs
    assert normal["task_success"] and normal["tool_calls"] == 1
    assert transient["task_success"] and transient["tool_calls"] == 3
    assert not persistent["task_success"]
    assert persistent["tool_calls"] == MAX_CALLS
    assert persistent["termination_reason"] == "call_cap_reached"

    output_folder = Path(__file__).resolve().parent / "results"
    output_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_path = output_folder / f"t1_baseline_{timestamp}.json"
    output_path.write_text(
        json.dumps(runs, indent=2),
        encoding="utf-8",
    )

    for run in runs:
        print(
            f"{run['scenario']}: "
            f"calls={run['tool_calls']}, "
            f"success={run['task_success']}, "
            f"reason={run['termination_reason']}"
        )

    print(f"\nLogs saved to: {output_path}")


if __name__ == "__main__":
    main()