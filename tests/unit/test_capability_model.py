# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T023/TB-T035/TB-T037: capability records carry state, evidence, and freshness."""
from trier_bridge.capability.model import Capability, CapabilityRecord, EnvironmentProfile
from trier_bridge.core.state import CapabilityState


def test_record_freshness_uses_monotonic_clock() -> None:
    rec = CapabilityRecord(Capability.SERVICE_MANAGER, CapabilityState.SUPPORTED, "systemd", "255")
    assert rec.is_fresh(rec.observed_monotonic + 10, ttl=60)
    assert not rec.is_fresh(rec.observed_monotonic + 61, ttl=60)


def test_plain_state_words_keep_states_distinct() -> None:
    words = {s: CapabilityRecord(Capability.JOURNAL, s, "x").plain_state for s in CapabilityState}
    assert len(set(words.values())) == len(CapabilityState)
    assert words[CapabilityState.UNKNOWN] == "Unknown"
    assert words[CapabilityState.ERROR] != words[CapabilityState.UNSUPPORTED]


def test_profile_session_facts_are_not_conflated() -> None:
    local = EnvironmentProfile(session_type="wayland", session_remote=False)
    remote = EnvironmentProfile(session_type="tty", session_remote=True)
    missing = EnvironmentProfile()
    assert local.is_graphical_local_session is True
    assert remote.is_graphical_local_session is False
    assert missing.is_graphical_local_session is None  # unknown stays unknown (TB-INV-023)


def test_profile_summary_shows_unknown_for_blanks() -> None:
    lines = EnvironmentProfile(distro_name="Ubuntu 24.04.5 LTS", distro_id="ubuntu").summary_lines()
    assert lines[0] == "Operating system: Ubuntu 24.04.5 LTS"
    assert "Kernel: Unknown" in lines
    assert "Remote session: Unknown" in lines
