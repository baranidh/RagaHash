"""
File Integrity Monitor — industry use-case demo
================================================
Use-case: Cybersecurity / DevOps / Compliance

Many industries (healthcare, finance, government) must detect unauthorised
file changes. This script uses RagaHash to build a baseline manifest of a
directory tree, then watches for changes and reports any tampered files.

Each raga produces a distinct hash, so you can tag your manifests with a
musical identity — "the production config signed under Keeravani" — and
verify it with the same raga to prevent cross-environment confusion.

Usage
-----
    # Build a baseline
    python examples/file_integrity_monitor.py baseline /etc/nginx

    # Check for changes (compare against the baseline)
    python examples/file_integrity_monitor.py check /etc/nginx

    # Watch continuously (checks every 30 seconds)
    python examples/file_integrity_monitor.py watch /etc/nginx --interval 30

    # Use a specific raga for signing
    python examples/file_integrity_monitor.py baseline /etc/nginx --raga 22

Industry applications
---------------------
- HIPAA / PCI-DSS file-change auditing
- CI/CD artefact integrity (build outputs haven't been tampered with)
- Configuration management: detect drift in /etc, systemd units, certs
- Software distribution: verify packages after download
- Forensic baselines: snapshot state before an incident investigation
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ragahash import ragahash, MELAKARTA_RAGAS, DEFAULT_RAGA


BASELINE_FILE = ".ragahash_baseline.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ansi(code, text):
    return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text

def ok(t):      return _ansi("32", t)
def fail(t):    return _ansi("31;1", t)
def warn(t):    return _ansi("33", t)
def dim(t):     return _ansi("2", t)
def bold(t):    return _ansi("1", t)
def gold(t):    return _ansi("33;1", t)


def hash_file(path: str, raga_id: int) -> str | None:
    try:
        with open(path, "rb") as f:
            return ragahash(f.read(), raga_id)
    except (PermissionError, OSError):
        return None


def scan_directory(root: str, raga_id: int) -> dict[str, dict]:
    """Return {relpath: {digest, size, mtime}} for all files under root."""
    manifest = {}
    for dirpath, _, filenames in os.walk(root):
        for fname in sorted(filenames):
            fpath = os.path.join(dirpath, fname)
            relpath = os.path.relpath(fpath, root)
            digest = hash_file(fpath, raga_id)
            try:
                stat = os.stat(fpath)
                size, mtime = stat.st_size, stat.st_mtime
            except OSError:
                size, mtime = 0, 0
            manifest[relpath] = {
                "digest": digest,
                "size": size,
                "mtime": mtime,
            }
    return manifest


def load_baseline(root: str) -> dict | None:
    path = os.path.join(root, BASELINE_FILE)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_baseline(root: str, data: dict) -> None:
    path = os.path.join(root, BASELINE_FILE)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_baseline(args):
    root = os.path.abspath(args.directory)
    raga_id = args.raga
    raga_name = MELAKARTA_RAGAS[raga_id]["name"]

    print(bold(f"\n  Building RagaHash baseline"))
    print(gold(f"  Raga  : {raga_id}. {raga_name}"))
    print(dim(f"  Root  : {root}\n"))

    manifest = scan_directory(root, raga_id)
    baseline = {
        "root": root,
        "raga_id": raga_id,
        "raga_name": raga_name,
        "created": datetime.now().isoformat(),
        "files": manifest,
    }
    save_baseline(root, baseline)

    for relpath, info in manifest.items():
        status = ok("  ✓") if info["digest"] else warn("  ?")
        digest_short = (info["digest"] or "error")[:16] + "…"
        size_str = f"{info['size']:>10} B"
        print(f"{status}  {gold(digest_short)}  {dim(size_str)}  {relpath}")

    print(gold(f"\n  Baseline saved: {os.path.join(root, BASELINE_FILE)}"))
    print(dim(f"  {len(manifest)} files indexed under raga {raga_id}. {raga_name}\n"))


def cmd_check(args) -> bool:
    root = os.path.abspath(args.directory)
    baseline = load_baseline(root)

    if baseline is None:
        print(fail(f"  No baseline found in {root}"))
        print(dim(f"  Run:  python {__file__} baseline {root}"))
        return False

    raga_id = baseline["raga_id"]
    raga_name = baseline["raga_name"]

    print(bold(f"\n  Checking integrity"))
    print(gold(f"  Raga      : {raga_id}. {raga_name}"))
    print(dim(f"  Baseline  : {baseline['created']}"))
    print(dim(f"  Root      : {root}\n"))

    current = scan_directory(root, raga_id)
    old_files = set(baseline["files"].keys()) - {BASELINE_FILE}
    new_files = set(current.keys()) - {BASELINE_FILE}

    added   = new_files - old_files
    removed = old_files - new_files
    changed = {
        p for p in old_files & new_files
        if current[p]["digest"] != baseline["files"][p]["digest"]
    }

    clean = True

    for p in sorted(changed):
        old_d = (baseline["files"][p]["digest"] or "?")[:16]
        new_d = (current[p]["digest"]           or "?")[:16]
        print(fail(f"  ✗ MODIFIED  ") + f"{p}")
        print(dim(f"              was: {old_d}…  now: {new_d}…"))
        clean = False

    for p in sorted(added):
        print(warn(f"  + ADDED     ") + f"{p}")
        clean = False

    for p in sorted(removed):
        print(warn(f"  - REMOVED   ") + f"{p}")
        clean = False

    if clean:
        print(ok(f"  ✓ All {len(old_files)} files intact — no changes detected"))
    else:
        total = len(changed) + len(added) + len(removed)
        print(fail(f"\n  {total} change(s) detected  ") +
              dim(f"({len(changed)} modified, {len(added)} added, {len(removed)} removed)"))

    print()
    return clean


def cmd_watch(args):
    interval = args.interval
    print(bold(f"\n  Watching {args.directory} every {interval}s  (Ctrl+C to stop)\n"))
    try:
        while True:
            clean = cmd_check(args)
            if not clean:
                # In a real system: send alert email/Slack/PagerDuty here
                print(warn("  [alert] Integrity violation — notify your security team!\n"))
            time.sleep(interval)
    except KeyboardInterrupt:
        print(dim("\n  Stopped.\n"))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        prog="file_integrity_monitor",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True)

    for cmd_name in ("baseline", "check", "watch"):
        sp = sub.add_parser(cmd_name)
        sp.add_argument("directory", help="Directory to monitor")
        sp.add_argument("--raga", type=int, default=DEFAULT_RAGA,
                        metavar="N", help=f"Melakarta raga ID 1–72 (default {DEFAULT_RAGA})")
        if cmd_name == "watch":
            sp.add_argument("--interval", type=int, default=30,
                            metavar="SEC", help="Seconds between checks (default 30)")

    args = p.parse_args()

    if args.command == "baseline":
        cmd_baseline(args)
    elif args.command == "check":
        ok_result = cmd_check(args)
        sys.exit(0 if ok_result else 1)
    elif args.command == "watch":
        cmd_watch(args)


if __name__ == "__main__":
    main()
