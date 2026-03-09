"""
ragahash CLI — python -m ragahash

Usage examples
--------------
# Hash a string
python -m ragahash "Hello, Carnatic world!"

# Hash a file
python -m ragahash --file /path/to/file.txt

# Hash stdin
echo "hello" | python -m ragahash -

# Choose a specific raga
python -m ragahash --raga 22 "hello"

# Show per-byte step trace
python -m ragahash --steps "hello"

# Export melody as WAV
python -m ragahash --wav melody.wav "hello"

# JSON output (for piping into other tools)
python -m ragahash --json "hello"

# List all 72 Melakarta ragas
python -m ragahash --list-ragas

# Hash every file in a directory and print a manifest
python -m ragahash --manifest /path/to/dir
"""

import argparse
import json
import os
import sys

from . import ragahash, ragahash_steps, ragachecksum, MELAKARTA_RAGAS, DEFAULT_RAGA
from .music import save_melody


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_input(args) -> tuple[bytes, str]:
    """Return (data_bytes, label) from the parsed args."""
    if args.file:
        path = args.file
        with open(path, "rb") as f:
            data = f.read()
        return data, path
    if args.message == "-":
        data = sys.stdin.buffer.read()
        return data, "<stdin>"
    return args.message.encode(), repr(args.message)


def _color(code: str, text: str) -> str:
    """Wrap text in ANSI colour if stdout is a TTY."""
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text


def _gold(t):  return _color("33", t)
def _green(t): return _color("32", t)
def _red(t):   return _color("31", t)
def _dim(t):   return _color("2",  t)
def _bold(t):  return _color("1",  t)


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def cmd_hash(args):
    data, label = _read_input(args)
    raga_id = args.raga

    digest = ragahash(data, raga_id)
    cs     = ragachecksum(data, raga_id)
    raga   = MELAKARTA_RAGAS[raga_id]

    if args.bare:
        print(digest)
        return

    if args.json:
        out = {
            "input":      label,
            "bytes":      len(data),
            "raga_id":    raga_id,
            "raga_name":  raga["name"],
            "digest":     digest,
            "checksum":   cs["hex"],
            "checksum_raga": cs["raga_name"],
        }
        print(json.dumps(out, indent=2))
        return

    print(_gold("━" * 64))
    print(_bold("  RagaHash-256"))
    print(_gold("━" * 64))
    print(f"  Input  : {_dim(label)}  ({len(data)} bytes)")
    raga_label = f"{raga_id}. {raga['name']}"
    print(f"  Raga   : {_green(raga_label)}")
    print(f"  Digest : {_gold(digest[:32])}")
    print(f"           {_gold(digest[32:])}")
    print(f"  Chksum : {cs['hex']}  {_dim('(' + cs['raga_name'] + ')')}")
    print(_gold("━" * 64))

    if args.steps:
        steps = ragahash_steps(data, raga_id)
        print(_bold("\n  Per-byte steps:"))
        for s in steps:
            bar = "▓" * int(s["note_freq"] / 50)
            print(f"  {s['char']!r:3s}  {s['swara_name']:16s}  {s['note_freq']:6.1f} Hz  {_gold(bar)}")
        print()

    if args.wav:
        steps = ragahash_steps(data, raga_id) if not args.steps else steps
        save_melody(steps, args.wav)


def cmd_list_ragas(args):
    print(_bold(f"  {'ID':>3}  {'Raga Name':<28}  Notes"))
    print(_dim("  " + "─" * 60))
    for rid, raga in MELAKARTA_RAGAS.items():
        notes_str = " ".join(str(n) for n in raga["notes"])
        marker = _gold("◆") if rid == DEFAULT_RAGA else " "
        print(f"  {marker}{rid:>3}  {raga['name']:<28}  {_dim(notes_str)}")
    print(_dim(f"\n  {DEFAULT_RAGA}. {MELAKARTA_RAGAS[DEFAULT_RAGA]['name']} is the default (◆)"))


def cmd_manifest(args):
    """Hash every file in a directory tree and print a manifest."""
    root = args.manifest
    if not os.path.isdir(root):
        print(_red(f"Error: {root!r} is not a directory"), file=sys.stderr)
        sys.exit(1)

    raga_id = args.raga
    raga_name = MELAKARTA_RAGAS[raga_id]["name"]

    rows = []
    for dirpath, _, filenames in os.walk(root):
        for fname in sorted(filenames):
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, "rb") as f:
                    data = f.read()
                digest = ragahash(data, raga_id)
                relpath = os.path.relpath(fpath, root)
                rows.append((relpath, digest, len(data)))
            except (PermissionError, OSError) as e:
                rows.append((os.path.relpath(fpath, root), f"ERROR: {e}", 0))

    if args.json:
        out = {
            "root": root,
            "raga_id": raga_id,
            "raga_name": raga_name,
            "files": [{"path": r, "digest": d, "bytes": b} for r, d, b in rows],
        }
        print(json.dumps(out, indent=2))
        return

    print(_bold(f"  RagaHash-256 manifest — raga {raga_id}. {raga_name}"))
    print(_gold("━" * 80))
    for relpath, digest, size in rows:
        if digest.startswith("ERROR"):
            print(f"  {_red(digest):52s}  {relpath}")
        else:
            print(f"  {_gold(digest[:16])}…{_gold(digest[-8:])}  {size:>10} B  {relpath}")
    print(_gold("━" * 80))
    print(_dim(f"  {len(rows)} file(s) in {root}"))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m ragahash",
        description="RagaHash-256: Carnatic Melakarta-inspired hashing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Input
    p.add_argument("message", nargs="?", default=None,
                   help="Message to hash (use '-' to read from stdin)")
    p.add_argument("-f", "--file", metavar="PATH",
                   help="Hash the contents of a file instead")
    p.add_argument("--manifest", metavar="DIR",
                   help="Hash every file in DIR and print a manifest")

    # Algorithm
    p.add_argument("-r", "--raga", type=int, default=DEFAULT_RAGA,
                   metavar="N", help=f"Melakarta raga ID 1–72 (default {DEFAULT_RAGA})")

    # Output modes
    p.add_argument("--steps",  action="store_true",
                   help="Print per-byte swara activation trace")
    p.add_argument("--wav",    metavar="FILE",
                   help="Export hash melody as a WAV file")
    p.add_argument("--json",   action="store_true",
                   help="Output results as JSON")
    p.add_argument("--bare",   action="store_true",
                   help="Print digest only (useful for scripting)")
    p.add_argument("--list-ragas", action="store_true",
                   help="List all 72 Melakarta ragas and exit")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not 1 <= args.raga <= 72:
        parser.error(f"--raga must be between 1 and 72, got {args.raga}")

    if args.list_ragas:
        cmd_list_ragas(args)
        return

    if args.manifest:
        cmd_manifest(args)
        return

    if args.message is None and not args.file:
        parser.print_help()
        sys.exit(0)

    cmd_hash(args)


if __name__ == "__main__":
    main()
