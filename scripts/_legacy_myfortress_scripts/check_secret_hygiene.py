import argparse
import os
import subprocess
import sys


BLOCKED_BASENAMES = {
    ".env",
    "credentials.json",
    "keystore.properties",
    "local.properties",
    "merlin-key",
    "token.pickle",
    "id_rsa",
    "id_ed25519",
}
BLOCKED_SUFFIXES = (".jks", ".keystore", ".p12", ".pem", ".key", ".pfx")
ALLOWLIST_BASENAMES = {".env.example", "keystore.properties.template"}


def _run_git(args):
    return subprocess.check_output(["git", *args], text=False)


def _is_truthy_env(name):
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _strict_mode_from_env():
    return (
        _is_truthy_env("SECRET_HYGIENE_STRICT")
        or _is_truthy_env("CI")
        or _is_truthy_env("GITHUB_ACTIONS")
    )


def _candidate_paths(include_all):
    if include_all:
        out = _run_git(["ls-files", "-z"])
    else:
        out = _run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"])
    if not out:
        return []
    return [part.decode("utf-8", errors="replace") for part in out.split(b"\x00") if part]


def _is_blocked(path):
    normalized = path.replace("\\", "/")
    basename = normalized.rsplit("/", 1)[-1]
    lowered = normalized.lower()

    if basename in ALLOWLIST_BASENAMES:
        return False
    if basename in BLOCKED_BASENAMES:
        return True
    if lowered.endswith(BLOCKED_SUFFIXES):
        return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Fail when tracked files match sensitive/local-only filename patterns."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check all tracked files instead of staged files only.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail closed if git metadata is unavailable.",
    )
    args = parser.parse_args()
    strict_mode = args.strict or _strict_mode_from_env()
    scope = "tracked" if args.all else "staged"

    try:
        candidates = _candidate_paths(include_all=args.all)
    except Exception as exc:
        if strict_mode:
            sys.stderr.write(
                f"Error: unable to inspect {scope} files for secret hygiene check: {exc}\n"
            )
            return 2
        # Preserve local-dev fallback behavior when strict mode is disabled.
        return 0

    violations = sorted(path for path in candidates if _is_blocked(path))
    if not violations:
        return 0

    sys.stderr.write(f"Error: {scope} files include sensitive/local-only paths:\n")
    for violation in violations:
        sys.stderr.write(f"  - {violation}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
