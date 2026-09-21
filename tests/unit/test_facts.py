# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T016/TB-T017/TB-T050: parsers for machine facts, fed with real file text."""
from pathlib import Path

from trier_bridge.capability.facts import (
    distro_from_os_release,
    parse_group_file,
    parse_os_release,
    parse_proc_stat_starttime,
)

UBUNTU = """PRETTY_NAME="Ubuntu 24.04.5 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.5 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
LOGO=ubuntu-logo
"""


def test_parse_os_release_from_a_real_file(tmp_path: Path) -> None:
    f = tmp_path / "os-release"
    f.write_text(UBUNTU, encoding="utf-8")
    fields = parse_os_release(f.read_text(encoding="utf-8"))
    assert fields["ID"] == "ubuntu" and fields["VERSION_ID"] == "24.04"
    assert fields["PRETTY_NAME"] == "Ubuntu 24.04.5 LTS"
    assert distro_from_os_release(fields) == ("ubuntu", "24.04", "Ubuntu 24.04.5 LTS", ("debian",))


def test_unknown_distro_stays_unknown() -> None:
    fields = parse_os_release('NAME="Something"\nPRETTY_NAME="Something Custom"\n')
    distro_id, version, pretty, like = distro_from_os_release(fields)
    assert distro_id == "" and version == "" and like == ()
    assert pretty == "Something Custom"  # name is shown, identity is not claimed (TB-INV-016)


def test_malformed_and_comment_lines_are_skipped() -> None:
    fields = parse_os_release(
        "# comment\n\nID=debian\nthis is not a field\nBAD KEY=x\nVERSION_ID='12'\n"
    )
    assert fields == {"ID": "debian", "VERSION_ID": "12"}


def test_escaped_quotes_are_unescaped() -> None:
    fields = parse_os_release('PRETTY_NAME="Distro \\"Quoted\\" 1"\n')
    assert fields["PRETTY_NAME"] == 'Distro "Quoted" 1'


def test_proc_stat_starttime_handles_spaces_in_comm() -> None:
    line = "4271 (Web Content) S 1 4271 4271 0 -1 4194560 100 0 0 0 5 3 0 0 20 0 30 0 296737 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25"
    assert parse_proc_stat_starttime(line) == 296737
    assert parse_proc_stat_starttime("garbage") is None


def test_group_membership_from_group_file(tmp_path: Path) -> None:
    f = tmp_path / "group"
    f.write_text(
        "root:x:0:\nadm:x:4:syslog,tb\nsudo:x:27:tb\nlxd:x:998:tb\nusers:x:100:\n", encoding="utf-8"
    )
    assert parse_group_file(f.read_text(encoding="utf-8"), "tb") == ("adm", "sudo", "lxd")
    assert parse_group_file(f.read_text(encoding="utf-8"), "nobody") == ()
