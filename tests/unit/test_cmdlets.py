# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T103/TB-T104: PowerShell names run the same typed operations; the rest teaches or refuses."""
from pathlib import Path

from trier_bridge.bridge.cmdlets import cmdlet_for, translate
from trier_bridge.bridge.commands import Exit, Session, run_line
from trier_bridge.bridge.grammar import Failure, ParseFailure, parse


def test_translation_table() -> None:
    assert translate(["Get-Process"]).tokens == ["tasklist"]
    assert translate(["gsv", "ssh"]).tokens == ["sc", "query", "ssh"]
    assert translate(["Get-Service", "-Name", "cups"]).tokens == ["sc", "query", "cups"]
    assert translate(["Stop-Process", "-Id", "42", "-Force"]).tokens == [
        "taskkill",
        "/pid",
        "/f",
        "42",
    ]
    assert translate(["Get-ChildItem", "-Path", "C:\\Users"]).tokens == ["dir", "C:\\Users"]
    assert translate(["gip"]).tokens == ["ipconfig", "/all"]
    assert translate(["Write-Output", "a", "b", "c"]).tokens == ["echo", "a", "b", "c"]
    assert translate(["tasklist"]).tokens == ["tasklist"] and translate(["tasklist"]).note == ""
    assert translate(["Get-Process"]).note == "Get-Process → tasklist"


def test_unknown_parameter_and_extra_arguments_refuse() -> None:
    bad = translate(["Get-Process", "-Name", "bash"])
    assert bad.failure and bad.failure_kind == "UNKNOWN_SWITCH" and bad.tokens == []
    missing = translate(["Stop-Process", "-Id"])
    assert missing.failure_kind == "MISSING_ARG"
    many = translate(["Get-Service", "a", "b"])
    assert many.failure_kind == "TOO_MANY_ARGS" and many.token == "b"
    assert isinstance(parse("Get-Process -Name bash"), ParseFailure)
    assert parse("Get-Process -Name bash").failure is Failure.UNKNOWN_SWITCH


def test_teach_only_cmdlets_and_shell_syntax() -> None:
    p = parse("Get-EventLog System")
    assert isinstance(p, ParseFailure) and p.failure is Failure.NO_EQUIVALENT
    assert "Event Viewer" in p.plain and "Nothing was run" in p.plain
    q = parse("$PSVersionTable")
    assert isinstance(q, ParseFailure) and q.failure is Failure.SHELL_SYNTAX
    assert cmdlet_for("gwmi") is not None and cmdlet_for("gwmi").teach


def test_cmdlet_runs_the_bridge_command_with_a_note(tmp_path: Path) -> None:
    session = Session(tmp_path)
    out = run_line("Get-Location", session)
    assert out.exit is Exit.OK
    assert out.lines[0] == "PowerShell Get-Location → cd"
    assert out.lines[1].startswith(str(tmp_path))  # plus the familiar spelling
    out = run_line("Set-Location -Path ..", session)
    assert out.exit is Exit.OK and session.cwd == tmp_path.parent
    helped = run_line("help Get-Service", session)
    assert helped.exit is Exit.OK and "sc query" in helped.lines[0]
    listing = run_line("help", session)
    assert any("Get-Process" in line for line in listing.lines)
    assert any("powershell" in line for line in listing.lines)


def test_powershell_entry_is_a_bridge_command() -> None:
    cmd = parse("powershell")
    assert not isinstance(cmd, ParseFailure) and cmd.spec.name == "powershell"
    assert parse("pwsh /x").failure is Failure.UNKNOWN_SWITCH  # type: ignore[union-attr]
