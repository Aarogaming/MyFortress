import argparse
import subprocess
import sys


BLOCKED_BASENAMES = {
    ".env",
    "credentials.json",
    "keystore.properties",
    "merlin-key",
    "token.pickle",
}
BLOCKED_SUFFIXES = (".jks", ".keystore", ".p12")
ALLOWLIST_BASENAMES = {".env.example"}


def _run_git(args):
    return subprocess.check_output(["git", *args], text=False)


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
    args = parser.parse_args()

    try:
        candidates = _candidate_paths(include_all=args.all)
    except Exception:
        # Don't block on environments where git metadata is unavailable.
        return 0

    violations = sorted(path for path in candidates if _is_blocked(path))
    if not violations:
        return 0

    scope = "tracked" if args.all else "staged"
    sys.stderr.write(f"Error: {scope} files include sensitive/local-only paths:\n")
    for violation in violations:
        sys.stderr.write(f"  - {violation}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
