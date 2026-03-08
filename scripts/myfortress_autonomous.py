#!/usr/bin/env python3
"""
MyFortress Autonomous Runner

Runs MyFortress maintenance tasks continuously with resource-aware throttling.
"""
import sys
from pathlib import Path

# Import shared framework from AAS core
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from autonomous_runner import (
    TaskSpec,
    build_parser,
    execute_autonomous_loop,
)


def build_tasks(args) -> list[TaskSpec]:
    """Define MyFortress maintenance tasks."""
    fortress_root = Path(__file__).resolve().parents[1]
    py = "python"
    scripts = fortress_root / "scripts"
    
    tasks = [
        TaskSpec(
            name="Check secret hygiene",
            command=[py, str(scripts / "check_secret_hygiene.py")],
            heavy=False,
        ),
        TaskSpec(
            name="Evaluate CP3 readiness",
            command=[py, str(scripts / "evaluate_cp3_readiness.py")],
            heavy=False,
        ),
        TaskSpec(
            name="Evaluate policy gate",
            command=[py, str(scripts / "evaluate_policy_gate.py")],
            heavy=False,
        ),
        TaskSpec(
            name="Check generated artifact shapes",
            command=[py, str(scripts / "check_generated_artifact_shapes.py")],
            heavy=False,
        ),
        TaskSpec(
            name="Generate policy trend snapshot",
            command=[py, str(scripts / "generate_policy_trend_snapshot.py")],
            heavy=False,
        ),
    ]
    
    return [t for t in tasks if t.enabled]


def main():
    parser = build_parser("MyFortress")
    args = parser.parse_args()
    fortress_root = Path(__file__).resolve().parents[1]
    execute_autonomous_loop("MyFortress", fortress_root, build_tasks, args)


if __name__ == "__main__":
    main()
