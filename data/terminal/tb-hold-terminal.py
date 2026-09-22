# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""Hold a terminal window open around one fixed program (ping, tracepath).

Trier Bridge launches this as a fixed argument list, never through a shell
(TB-SEC-003, TB-INV-088)::

    python3 tb-hold-terminal.py <marker-file> -- <program> [args...]

It writes its own pid to <marker-file> so Trier Bridge can close this window
before opening the next one, runs the program with its arguments exactly as
given (a list handed to the operating system, not text handed to a shell),
then waits for Enter so the replies stay readable. Nothing here reads or
changes anything else on the computer.
"""
import os
import subprocess  # list form only; no shell anywhere in this file
import sys


def main(argv: list[str]) -> int:
    if len(argv) < 4 or argv[2] != "--":
        print("usage: tb-hold-terminal.py <marker-file> -- <program> [args...]", file=sys.stderr)
        return 2
    marker, program = argv[1], argv[3:]
    try:
        with open(marker, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
    except OSError:
        pass  # window reuse degrades to "one more window"; the program still runs
    try:
        status = subprocess.run(program, check=False).returncode
    except OSError as exc:
        print(f"{program[0]}: {exc.strerror or exc}", file=sys.stderr)
        status = 127
    print()
    try:
        input("Press Enter to close... ")
    except EOFError:
        pass
    return status if 0 <= status < 256 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
