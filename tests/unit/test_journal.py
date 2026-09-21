# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T068/TB-T100/TB-T144/TB-T147: journal text is data, views are filters, provenance survives."""
from trier_bridge.system.journal import Entry, Level, View, level_for_priority, sanitize


def test_sanitize_strips_ansi_and_control_but_keeps_text() -> None:
    hostile = "\x1b[31mred\x1b[0m alert\x07 \x1b]0;title\x07 tab\there\nnext\r"
    out = sanitize(hostile)
    assert "\x1b" not in out and "\x07" not in out and "\n" not in out
    assert "red" in out and "alert" in out and "tab here next" in out
    assert sanitize("plain unicode: café ✓") == "plain unicode: café ✓"


def test_priority_maps_to_levels_and_unknown_stays_unknown() -> None:
    assert level_for_priority("0") is Level.ERROR and level_for_priority("3") is Level.ERROR
    assert level_for_priority("4") is Level.WARNING
    assert level_for_priority("6") is Level.INFORMATION
    assert level_for_priority("7") is Level.DEBUG
    assert level_for_priority(None) is Level.UNKNOWN
    assert level_for_priority("high") is Level.UNKNOWN


def _entry(**fields: str) -> Entry:
    return Entry(
        realtime_usec=1,
        level=level_for_priority(fields.get("PRIORITY")),
        message=fields.get("MESSAGE", ""),
        source=fields.get("_SYSTEMD_UNIT") or fields.get("SYSLOG_IDENTIFIER", "?"),
        fields=fields,
    )


def test_views_are_filters_over_native_fields() -> None:
    kernel = _entry(MESSAGE="usb 1-1: new device", _TRANSPORT="kernel", PRIORITY="6")
    system = _entry(
        MESSAGE="Started CUPS", _SYSTEMD_UNIT="cups.service", _TRANSPORT="journal", PRIORITY="6"
    )
    user_app = _entry(
        MESSAGE="window shown",
        _SYSTEMD_USER_UNIT="app-firefox.scope",
        _TRANSPORT="stdout",
        PRIORITY="6",
    )
    auth = _entry(
        MESSAGE="pam_unix(sudo:session)",
        SYSLOG_IDENTIFIER="sudo",
        _TRANSPORT="syslog",
        PRIORITY="6",
    )
    err = _entry(
        MESSAGE="Failed to start x", _SYSTEMD_UNIT="x.service", _TRANSPORT="journal", PRIORITY="3"
    )
    assert kernel.matches(View.BOOT) and not kernel.matches(View.SYSTEM)
    assert system.matches(View.SYSTEM) and not system.matches(View.APPLICATION)
    assert user_app.matches(View.APPLICATION) and not user_app.matches(View.SYSTEM)
    assert auth.matches(View.SECURITY) and auth.matches(View.APPLICATION)
    assert err.matches(View.ERRORS) and err.matches(View.SYSTEM)
    assert all(e.matches(View.ALL) for e in (kernel, system, user_app, auth, err))
    # native fields survive untouched alongside the familiar view (TB-INV-147)
    assert system.fields["_SYSTEMD_UNIT"] == "cups.service"
