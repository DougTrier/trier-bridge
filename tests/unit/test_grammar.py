# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T083..089, TB-T105: the Bridge grammar parses strictly and never yields a shell string."""
import pytest

from trier_bridge.bridge.grammar import BridgeCommand, Failure, ParseFailure, parse, tokenize
from trier_bridge.core.state import PrivilegeClass


def test_valid_commands_become_typed() -> None:
    cmd = parse("ipconfig /all")
    assert isinstance(cmd, BridgeCommand)
    assert cmd.spec.name == "ipconfig" and cmd.switches == ("all",) and cmd.args == ()
    assert cmd.spec.privilege is PrivilegeClass.A_READ_ONLY
    tk = parse("TASKKILL /PID 4271 /F")
    assert isinstance(tk, BridgeCommand)
    assert tk.spec.name == "taskkill" and tk.switches == ("pid", "f") and tk.args == ("4271",)
    assert tk.spec.privilege is PrivilegeClass.B_USER_MUTATION
    assert isinstance(parse("sc query cups"), BridgeCommand)
    assert isinstance(parse("ipconfig.exe"), BridgeCommand)


@pytest.mark.parametrize(
    "line",
    [
        "taskkill /PID 1234; rm -rf /",
        "ipconfig && whoami",
        "dir | findstr x",
        "echo hi > out.txt",
        "tasklist `id`",
        "echo $(id)",
        "type $HOME/file",
        "ver ^ hidden",
    ],
)
def test_shell_syntax_is_rejected_as_a_whole(line: str) -> None:
    res = parse(line)
    assert isinstance(res, ParseFailure) and res.failure is Failure.SHELL_SYNTAX
    assert not res.performed and "Nothing was run" in res.plain


def test_unknown_command_and_switch_and_residue() -> None:
    r = parse("frobnicate now")
    assert isinstance(r, ParseFailure) and r.failure is Failure.UNKNOWN_COMMAND
    r = parse("ipconfig /nope")
    assert (
        isinstance(r, ParseFailure) and r.failure is Failure.UNKNOWN_SWITCH and r.token == "/nope"
    )
    r = parse("whoami extra")
    assert isinstance(r, ParseFailure) and r.failure is Failure.TOO_MANY_ARGS
    r = parse("taskkill /f")
    assert isinstance(r, ParseFailure) and r.failure is Failure.MISSING_ARG


def test_no_equivalent_commands_never_execute() -> None:
    for line in ("regedit", "format c:"):
        r = parse(line)
        assert isinstance(r, ParseFailure) and r.failure is Failure.NO_EQUIVALENT


def test_quoting_and_unicode_are_preserved_without_injection() -> None:
    assert tokenize('type "My Documents\\notes.txt"') == ["type", "My Documents\\notes.txt"]
    assert tokenize('echo "say ""hi"" now"') == ["echo", 'say "hi" now']
    cmd = parse('echo café ✓ "and more"')
    assert isinstance(cmd, BridgeCommand) and cmd.args == ("café", "✓", "and more")
    r = parse('type "unterminated')
    assert isinstance(r, ParseFailure) and r.failure is Failure.BAD_QUOTING
    r = parse("dir \x1b[31m")
    assert isinstance(r, ParseFailure) and r.failure is Failure.BAD_ENCODING


def test_length_and_empty() -> None:
    assert parse("").failure is Failure.EMPTY  # type: ignore[union-attr]
    r = parse("echo " + "x" * 5000)
    assert isinstance(r, ParseFailure) and r.failure is Failure.TOO_LONG
