#!/usr/bin/env python3
"""
Local secrets scanner for pre-commit.

Scans provided files for common secret patterns and blocks commits when
potential secrets are detected.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

API_KEY_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("openai_project_key", re.compile(r"sk-proj-[A-Za-z0-9]{20,}")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("github_oauth", re.compile(r"gho_[A-Za-z0-9]{36}")),
    ("linear_api", re.compile(r"lin_api_[A-Za-z0-9]{40}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]+")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z\\-_]{35}")),
]

PRIVATE_KEY_MARKERS = [
    "BEGIN PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
    "BEGIN DSA PRIVATE KEY",
    "BEGIN EC PRIVATE KEY",
    "BEGIN OPENSSH PRIVATE KEY",
]

CREDENTIAL_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    (
        "password_assignment",
        re.compile(r'password\\s*[=:]\\s*["\'][^"\']{3,}["\']', re.IGNORECASE),
    ),
    (
        "token_assignment",
        re.compile(r'token\\s*[=:]\\s*["\'][^"\']{10,}["\']', re.IGNORECASE),
    ),
    (
        "secret_assignment",
        re.compile(r'secret\\s*[=:]\\s*["\'][^"\']{10,}["\']', re.IGNORECASE),
    ),
]

PRIVATE_KEY_PATH_EXCLUSIONS = ("scan_for_secrets", "apisender", "handoffutility")


def is_env_file(path: Path) -> bool:
    return path.name == ".env"


def should_skip_credential_scan(path: Path) -> bool:
    name = path.name.lower()
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or name == "conftest.py"
        or name.endswith(".example")
        or name.endswith(".md")
    )


def should_skip_private_key(path: Path) -> bool:
    lowered = str(path).lower()
    return any(token in lowered for token in PRIVATE_KEY_PATH_EXCLUSIONS)


def iter_lines(path: Path) -> Iterable[Tuple[int, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return enumerate(text.splitlines(), start=1)


def scan_file(path: Path, max_matches: int) -> List[str]:
    issues: List[str] = []
    skip_creds = should_skip_credential_scan(path)
    skip_private_keys = should_skip_private_key(path)

    for line_number, line in iter_lines(path):
        for label, pattern in API_KEY_PATTERNS:
            if pattern.search(line):
                issues.append(f"Potential {label} in {path}:{line_number}")
                if len(issues) >= max_matches:
                    return issues

        if not skip_private_keys:
            for marker in PRIVATE_KEY_MARKERS:
                if marker in line:
                    issues.append(f"Private key marker in {path}:{line_number}")
                    if len(issues) >= max_matches:
                        return issues

        if not skip_creds:
            for label, pattern in CREDENTIAL_PATTERNS:
                if pattern.search(line):
                    issues.append(f"Potential {label} in {path}:{line_number}")
                    if len(issues) >= max_matches:
                        return issues

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan files for secrets.")
    parser.add_argument("files", nargs="*", help="Files to scan")
    parser.add_argument("--max-matches", type=int, default=50)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.files:
        print("No files to scan.")
        return 0

    issues: List[str] = []
    env_files: List[Path] = []

    for raw_path in args.files:
        path = Path(raw_path)
        if is_env_file(path):
            env_files.append(path)
            continue
        if not path.exists() or path.is_dir():
            continue
        remaining = args.max_matches - len(issues)
        if remaining <= 0:
            break
        issues.extend(scan_file(path, remaining))
        if len(issues) >= args.max_matches:
            break

    if env_files:
        for env_path in env_files:
            issues.append(f".env file detected: {env_path}")

    if not issues:
        print("No secrets detected.")
        return 0

    print("Potential secrets found:")
    for issue in issues:
        print(f"  - {issue}")
    print("Review and remove secrets before committing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
