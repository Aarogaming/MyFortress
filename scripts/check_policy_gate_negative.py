import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT_DIR / "scripts/evaluate_policy_gate.py"


def _run_negative_check(envelope: str, expected_signature: str) -> str | None:
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--envelope",
        envelope,
    ]
    result = subprocess.run(
        cmd,
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        check=False,
    )
    output = f"{result.stdout}{result.stderr}"

    if result.returncode == 0:
        return f"{envelope}: expected non-zero exit but command passed"
    if "POLICY_GATE_FAIL" not in output:
        return f"{envelope}: missing POLICY_GATE_FAIL marker"
    if expected_signature not in output:
        return f"{envelope}: expected signature {expected_signature!r} not found"
    return None


def main() -> int:
    checks = [
        (
            "artifacts/policy/envelope_negative_out_of_scope.json",
            "outside allowlist",
        ),
        (
            "artifacts/policy/envelope_negative_bad_transition.json",
            "not allowed",
        ),
        (
            "artifacts/policy/envelope_negative_missing_attestation.json",
            "sbom_attestation",
        ),
        (
            "artifacts/policy/envelope_negative_schema_invalid.json",
            "schema validation failed",
        ),
    ]

    errors: list[str] = []
    for envelope, expected_signature in checks:
        error = _run_negative_check(
            envelope=envelope,
            expected_signature=expected_signature,
        )
        if error:
            errors.append(error)

    if errors:
        sys.stderr.write("POLICY_GATE_NEGATIVE_FAIL\n")
        for error in errors:
            sys.stderr.write(f"- {error}\n")
        return 2

    print("POLICY_GATE_NEGATIVE_PASS")
    for envelope, _ in checks:
        print(f"envelope={envelope}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
