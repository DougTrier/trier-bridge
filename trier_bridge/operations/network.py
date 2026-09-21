# Copyright 2026 Doug Trier
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Network changes as typed operations: the translation layer (DEC-024, IMP-06.06).

What a Windows user does in Network Connections or with ``netsh`` becomes a
NetworkManager change: disconnect or connect an adapter, give it a fixed IPv4
address (with gateway and DNS), or set it back to automatic. Every change is a
class C operation: previewed, confirmed, then one D-Bus call with
ALLOW_INTERACTIVE_AUTHORIZATION so polkit decides and prompts (TB-INV-109,
TB-INV-110). The connection is revalidated by UUID right before acting
(TB-INV-052), and success is the observed device state or the re-read
settings, never the return code alone (TB-INV-006).
"""
from __future__ import annotations

import ipaddress
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

from ..core.identity import ConnectionIdentity  # noqa: E402
from ..core.operations import Operation, OperationResult  # noqa: E402
from ..core.state import OperationState, PrivilegeClass  # noqa: E402
from ..state.journal import OperationJournal  # noqa: E402
from ..system.bus import Bus  # noqa: E402
from ..system.network import NM, NM_PATH, NetworkDevice, read_network  # noqa: E402

CALL_TIMEOUT_MS = 30000
VERIFY_TIMEOUT_S = 12.0
SETTINGS_IFACE = f"{NM}.Settings.Connection"
ACTIVE_IFACE = f"{NM}.Connection.Active"
DEVICE_IFACE = f"{NM}.Device"

VERBS: dict[str, str] = {
    "disconnect": "Disconnect",
    "connect": "Connect",
    "static": "Use a fixed IPv4 address",
    "auto": "Get the IPv4 address automatically",
    "dns": "Use these DNS servers",
    "dns-auto": "Get DNS servers automatically",
}


@dataclass(frozen=True)
class IPv4Settings:
    address: str
    prefix: int
    gateway: str = ""
    dns: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class NetworkPlan:
    operation: Operation
    verb: str
    device: NetworkDevice
    identity: ConnectionIdentity
    settings: IPv4Settings | None
    dns: tuple[str, ...]
    preview: str
    needs_admin: bool = True

    @property
    def label(self) -> str:
        return self.device.interface

    @property
    def heading(self) -> str:
        return VERBS[self.verb]


# ---- validation helpers (pure) --------------------------------------------------------


def parse_ipv4(text: str) -> str:
    """A dotted IPv4 address, or ValueError with a plain reason."""
    try:
        return str(ipaddress.IPv4Address(text.strip()))
    except (ValueError, ipaddress.AddressValueError) as exc:
        raise ValueError(f"'{text}' is not an IPv4 address.") from exc


def mask_to_prefix(mask: str) -> int:
    """255.255.255.0 -> 24; a prefix length given as a number is accepted too."""
    text = mask.strip()
    if text.isdigit():
        n = int(text)
        if 0 <= n <= 32:
            return n
        raise ValueError(f"'{mask}' is not a valid prefix length (0-32).")
    try:
        net = ipaddress.IPv4Network(f"0.0.0.0/{text}")
    except (ValueError, ipaddress.NetmaskValueError) as exc:
        raise ValueError(f"'{mask}' is not a valid subnet mask.") from exc
    return net.prefixlen


def ipv4_settings(
    address: str, mask_or_prefix: str, gateway: str = "", dns: str = ""
) -> IPv4Settings:
    """Validate what a person typed (Windows order: address, mask, gateway) into settings."""
    if "/" in address and not mask_or_prefix:
        address, mask_or_prefix = address.split("/", 1)
    addr = parse_ipv4(address)
    prefix = mask_to_prefix(mask_or_prefix) if mask_or_prefix else 24
    gw = parse_ipv4(gateway) if gateway.strip() else ""
    servers = tuple(parse_ipv4(s) for s in dns.replace(";", ",").split(",") if s.strip())
    return IPv4Settings(addr, prefix, gw, servers)


def _dns_u32(address: str) -> int:
    """NetworkManager stores IPv4 DNS servers as uint32 in network byte order."""
    return int(struct.unpack("<I", socket.inet_aton(address))[0])


# ---- planning ----------------------------------------------------------------------


def _refuse(
    op: Operation, state: OperationState, plain: str, next_step: str = ""
) -> OperationResult:
    return OperationResult(op.operation_id, state, plain, safest_next_step=next_step)


def plan_network(
    device: NetworkDevice,
    verb: str,
    settings: IPv4Settings | None = None,
    dns: tuple[str, ...] = (),
) -> NetworkPlan | OperationResult:
    if verb not in VERBS:
        raise ValueError(f"unknown network verb {verb}")
    identity = ConnectionIdentity(uuid=device.connection_uuid, interface=device.interface)
    op = Operation(
        kind=f"network.{verb}",
        target=identity,
        privilege=PrivilegeClass.C_ADMIN_MUTATION,
        parameters={
            "interface": device.interface,
            "uuid": device.connection_uuid,
            "settings": str(settings) if settings else "",
            "dns": ",".join(dns),
        },
    )
    name = device.interface
    if device.is_loopback:
        return _refuse(op, OperationState.UNSUPPORTED, "The loopback adapter cannot be changed.")
    if device.managed is False:
        return _refuse(
            op,
            OperationState.UNSUPPORTED,
            f"{name} is not managed by NetworkManager, so Trier Bridge cannot change it. "
            "Nothing was changed.",
        )
    profile = device.connection_name or "its connection"
    asks = " Linux will ask for administrator permission for this one change."
    if verb == "connect":
        if device.connection_uuid:
            return _refuse(
                op, OperationState.UNSUPPORTED, f"{name} is already connected to {profile}."
            )
        preview = f"Connect {name} using its saved connection profile?{asks}"
        return NetworkPlan(op.with_preview(preview), verb, device, identity, None, (), preview)
    if not device.connection_uuid:
        return _refuse(
            op,
            OperationState.UNSUPPORTED,
            f"{name} has no active connection to change. Connect it first. Nothing was changed.",
        )
    if verb == "disconnect":
        preview = (
            f"Disconnect {name} from {profile}? The computer loses this network link until you "
            f"connect it again.{asks}"
        )
    elif verb == "static":
        if settings is None:
            raise ValueError("static needs IPv4 settings")
        gw = f", gateway {settings.gateway}" if settings.gateway else ""
        servers = f", DNS {', '.join(settings.dns)}" if settings.dns else ""
        preview = (
            f"Give {name} ({profile}) the fixed address {settings.address}/{settings.prefix}{gw}"
            f"{servers}? The change is saved in the connection profile and applied now.{asks}"
        )
    elif verb == "auto":
        preview = (
            f"Set {name} ({profile}) to get its IPv4 address automatically (DHCP)? The fixed "
            f"address is removed from the profile and the adapter asks the network.{asks}"
        )
    elif verb == "dns":
        if not dns:
            raise ValueError("dns needs at least one server")
        preview = (
            f"Use {', '.join(dns)} as the DNS servers for {name} ({profile}) instead of the "
            f"ones the network hands out?{asks}"
        )
    else:  # dns-auto
        preview = f"Let {name} ({profile}) use the DNS servers the network hands out?{asks}"
    return NetworkPlan(op.with_preview(preview), verb, device, identity, settings, dns, preview)


# ---- execution -----------------------------------------------------------------------


def _nm_call(bus: Bus, path: str, iface: str, method: str, args: Any) -> tuple[Any, str]:
    """One NetworkManager call, letting polkit prompt interactively."""
    if bus.conn is None:
        return None, bus.error or "bus unavailable"
    try:
        res = bus.conn.call_sync(
            NM,
            path,
            iface,
            method,
            args,
            None,
            Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION,
            CALL_TIMEOUT_MS,
            None,
        )
        return res, ""
    except GLib.Error as exc:
        return None, f"{exc.domain}: {exc.message}"


def _classify_error(err: str) -> tuple[OperationState, str]:
    low = err.lower()
    if "accessdenied" in low or "not authorized" in low or "permissiondenied" in low:
        return OperationState.DENIED, "Linux did not grant permission for this change."
    if "cancel" in low or "dismissed" in low:
        return OperationState.CANCELLED, "The permission request was cancelled."
    if "timeout" in low or "timed out" in low:
        return OperationState.OUTCOME_UNKNOWN, "NetworkManager did not answer in time."
    return OperationState.FAILED, "NetworkManager refused the change."


def _settings_dict(variant: GLib.Variant) -> dict[str, dict[str, GLib.Variant]]:
    """GetSettings() as {section: {key: Variant}} with every value's type kept."""
    out: dict[str, dict[str, GLib.Variant]] = {}
    outer = variant.get_child_value(0)
    for i in range(outer.n_children()):
        entry = outer.get_child_value(i)
        section = entry.get_child_value(0).get_string()
        inner = entry.get_child_value(1)
        values: dict[str, GLib.Variant] = {}
        for j in range(inner.n_children()):
            kv = inner.get_child_value(j)
            values[kv.get_child_value(0).get_string()] = kv.get_child_value(1).get_variant()
        out[section] = values
    return out


def _fresh_device(bus: Bus, plan: NetworkPlan) -> NetworkDevice | None:
    nw = read_network(bus)
    if plan.device.object_path:
        hit = next((d for d in nw.devices if d.object_path == plan.device.object_path), None)
        if hit is not None:
            return hit
    # software adapters (dummy, bridge, VPN) come and go with their connection: match by name
    return next((d for d in nw.devices if d.interface == plan.device.interface), None)


def _saved_profile(bus: Bus, interface: str) -> tuple[str, str, str]:
    """(object path, uuid, id) of the saved profile bound to this interface name, or empties."""
    res, err = bus.call(NM, f"{NM_PATH}/Settings", f"{NM}.Settings", "ListConnections")
    if err or not res:
        return "", "", ""
    for path in res[0]:
        raw, err = _nm_call(bus, str(path), SETTINGS_IFACE, "GetSettings", None)
        if err:
            continue
        conn = _settings_dict(raw).get("connection", {})
        name = conn["interface-name"].get_string() if "interface-name" in conn else ""
        if name == interface:
            uuid = conn["uuid"].get_string() if "uuid" in conn else ""
            ident = conn["id"].get_string() if "id" in conn else ""
            return str(path), uuid, ident
    return "", "", ""


def plan_connect(interface: str, bus: Bus | None = None) -> NetworkPlan | OperationResult:
    """Connect an adapter that is not listed right now (a virtual one NetworkManager removed
    when it was disconnected) from its saved profile."""
    bus = bus or Bus.system()
    path, uuid, ident = _saved_profile(bus, interface)
    device = NetworkDevice(
        interface=interface,
        kind="Unknown",
        link_state="Not present",
        managed=None,
        driver="",
        mac="",
        connection_name=ident,
        connection_uuid="",
        identity=None,
        ipv4=(),
        ipv6=(),
        gateway4="",
        dns=(),
        object_path="",
    )
    op = Operation(
        kind="network.connect",
        target=ConnectionIdentity(uuid=uuid, interface=interface),
        privilege=PrivilegeClass.C_ADMIN_MUTATION,
        parameters={"interface": interface, "uuid": uuid, "profile": path},
    )
    if not path:
        return _refuse(
            op,
            OperationState.UNSUPPORTED,
            f"No adapter named '{interface}' is present and no saved connection profile is "
            "bound to that name. Nothing was changed.",
        )
    preview = (
        f"Connect {interface} using its saved profile '{ident}'? Linux will ask for "
        "administrator permission for this one change."
    )
    return NetworkPlan(
        op.with_preview(preview),
        "connect",
        device,
        ConnectionIdentity(uuid=uuid, interface=interface),
        None,
        (),
        preview,
    )


def _profile_path(bus: Bus, device_path: str) -> str:
    ac_path, err = bus.property(NM, device_path, DEVICE_IFACE, "ActiveConnection")
    if err or not ac_path or ac_path == "/":
        return ""
    conn_path, err = bus.property(NM, str(ac_path), ACTIVE_IFACE, "Connection")
    return "" if err or not conn_path else str(conn_path)


def _apply_ipv4(bus: Bus, plan: NetworkPlan, profile: str) -> str:
    """Update the profile's ipv4 section and reapply it to the device. Returns an error text."""
    raw, err = _nm_call(bus, profile, SETTINGS_IFACE, "GetSettings", None)
    if err:
        return err
    settings = _settings_dict(raw)
    ipv4 = dict(settings.get("ipv4", {}))
    for legacy in ("addresses", "routes"):
        ipv4.pop(legacy, None)
    if plan.verb == "static" and plan.settings is not None:
        s = plan.settings
        ipv4["method"] = GLib.Variant("s", "manual")
        ipv4["address-data"] = GLib.Variant(
            "aa{sv}",
            [{"address": GLib.Variant("s", s.address), "prefix": GLib.Variant("u", s.prefix)}],
        )
        if s.gateway:
            ipv4["gateway"] = GLib.Variant("s", s.gateway)
        else:
            ipv4.pop("gateway", None)
        if s.dns:
            ipv4["dns"] = GLib.Variant("au", [_dns_u32(x) for x in s.dns])
            ipv4["ignore-auto-dns"] = GLib.Variant("b", True)
    elif plan.verb == "auto":
        ipv4["method"] = GLib.Variant("s", "auto")
        ipv4["address-data"] = GLib.Variant("aa{sv}", [])
        ipv4.pop("gateway", None)
    elif plan.verb == "dns":
        ipv4["dns"] = GLib.Variant("au", [_dns_u32(x) for x in plan.dns])
        ipv4["ignore-auto-dns"] = GLib.Variant("b", True)
    else:  # dns-auto
        ipv4["dns"] = GLib.Variant("au", [])
        ipv4["ignore-auto-dns"] = GLib.Variant("b", False)
    settings["ipv4"] = ipv4
    _, err = _nm_call(
        bus, profile, SETTINGS_IFACE, "Update", GLib.Variant("(a{sa{sv}})", (settings,))
    )
    if err:
        return err
    _, err = _nm_call(
        bus,
        plan.device.object_path,
        DEVICE_IFACE,
        "Reapply",
        GLib.Variant("(a{sa{sv}}tu)", ({}, 0, 0)),
    )
    return err


def _settings_show(bus: Bus, profile: str) -> tuple[str, list[str], list[str]]:
    """(method, addresses, dns) as NetworkManager now stores them."""
    raw, err = _nm_call(bus, profile, SETTINGS_IFACE, "GetSettings", None)
    if err:
        return "", [], []
    ipv4 = _settings_dict(raw).get("ipv4", {})
    method = ipv4["method"].get_string() if "method" in ipv4 else ""
    addresses = []
    if "address-data" in ipv4:
        for entry in ipv4["address-data"].unpack():
            addresses.append(f"{entry.get('address', '')}/{entry.get('prefix', '')}")
    dns = []
    if "dns" in ipv4:
        for n in ipv4["dns"].unpack():
            dns.append(socket.inet_ntoa(struct.pack("<I", int(n))))
    return method, addresses, dns


def execute_network(
    plan: NetworkPlan, journal: OperationJournal | None = None, bus: Bus | None = None
) -> OperationResult:
    bus = bus or Bus.system()
    op = plan.operation
    name = plan.device.interface
    rec = None
    if journal is not None:
        rec = journal.open(
            op.operation_id,
            op.kind,
            "network",
            name,
            {"interface": name, "uuid": plan.identity.uuid, "device": plan.device.object_path},
            plan.preview,
        )
        journal.advance(rec, OperationState.PREVIEWED)

    def advance(state: OperationState) -> None:
        if journal is not None and rec is not None:
            journal.advance(rec, state)

    def finish(
        state: OperationState,
        plain: str,
        technical: str = "",
        next_step: str = "",
        succeeded: tuple[str, ...] = (),
        failed: tuple[str, ...] = (),
    ) -> OperationResult:
        if journal is not None and rec is not None:
            journal.advance(rec, state, plain, technical)
        return OperationResult(
            op.operation_id, state, plain, technical, next_step, succeeded, failed
        )

    # Revalidate: same adapter, same active connection as when it was shown (TB-INV-052).
    fresh = _fresh_device(bus, plan)
    if (fresh is None or fresh.interface != name) and plan.verb != "connect":
        return finish(
            OperationState.CANCELLED, f"{name} is no longer present. Nothing was changed."
        )
    if plan.verb == "connect" and fresh is not None and fresh.connection_uuid:
        return finish(
            OperationState.CANCELLED, f"{name} connected in the meantime. Nothing was changed."
        )
    if plan.verb != "connect" and (fresh is None or fresh.connection_uuid != plan.identity.uuid):
        return finish(
            OperationState.CANCELLED,
            f"{name} changed its connection since it was shown. Nothing was changed.",
            next_step="Refresh Network and try again.",
        )
    advance(OperationState.EXECUTING)
    if plan.verb == "disconnect":
        _, err = _nm_call(bus, plan.device.object_path, DEVICE_IFACE, "Disconnect", None)
    elif plan.verb == "connect":
        profile = plan.operation.parameters.get("profile", "") or "/"
        device_path = plan.device.object_path or "/"
        _, err = _nm_call(
            bus,
            NM_PATH,
            NM,
            "ActivateConnection",
            GLib.Variant("(ooo)", (profile, device_path, "/")),
        )
    else:
        profile = _profile_path(bus, plan.device.object_path)
        if not profile:
            return finish(
                OperationState.CANCELLED, f"{name} has no connection profile to change any more."
            )
        err = _apply_ipv4(bus, plan, profile)
    if err:
        state, plain = _classify_error(err)
        return finish(state, f"{plain} {name} was not changed.", err)
    advance(OperationState.COMMITTED)
    advance(OperationState.VERIFYING)
    return _verify(bus, plan, finish)


def _verify(bus: Bus, plan: NetworkPlan, finish: Callable[..., OperationResult]) -> OperationResult:
    name = plan.device.interface
    deadline = time.monotonic() + VERIFY_TIMEOUT_S
    last = ""
    if plan.verb in ("disconnect", "connect"):
        while time.monotonic() < deadline:
            fresh = _fresh_device(bus, plan)
            last = fresh.link_state if fresh else "gone"
            if plan.verb == "disconnect" and fresh is None:
                return finish(
                    OperationState.VERIFIED,
                    f"{name} is disconnected; the virtual adapter is removed until it "
                    "connects again.",
                    "Device.Disconnect ok; software device unrealized",
                )
            if plan.verb == "disconnect" and fresh is not None and not fresh.connection_uuid:
                return finish(
                    OperationState.VERIFIED,
                    f"{name} is disconnected ({fresh.link_state}).",
                    "Device.Disconnect ok; ActiveConnection cleared",
                )
            if plan.verb == "connect" and fresh is not None and fresh.link_state == "Connected":
                return finish(
                    OperationState.VERIFIED,
                    f"{name} is connected to {fresh.connection_name} "
                    f"({', '.join(fresh.ipv4) or 'no IPv4 address yet'}).",
                    "ActivateConnection ok; State=100",
                )
            if fresh is not None and fresh.link_state == "Failed":
                return finish(
                    OperationState.FAILED,
                    f"{name} could not connect (NetworkManager reports Failed).",
                    "State=120",
                    "Check the connection profile in Settings.",
                )
            time.sleep(0.5)
        return finish(
            OperationState.OUTCOME_UNKNOWN,
            f"{name} was asked to {plan.verb} but reports '{last}' after "
            f"{int(VERIFY_TIMEOUT_S)} seconds.",
            "verify timeout",
            "Refresh Network in a moment.",
        )
    profile = _profile_path(bus, plan.device.object_path)
    method, addresses, dns = _settings_show(bus, profile) if profile else ("", [], [])
    if plan.verb == "static" and plan.settings is not None:
        want = f"{plan.settings.address}/{plan.settings.prefix}"
        if method != "manual" or want not in addresses:
            return finish(
                OperationState.FAILED,
                f"The profile for {name} did not keep the fixed address.",
                f"method={method} addresses={addresses}",
            )
        while time.monotonic() < deadline:
            fresh = _fresh_device(bus, plan)
            if fresh is not None and want in fresh.ipv4:
                return finish(
                    OperationState.VERIFIED,
                    f"{name} now uses {want}"
                    + (f" with gateway {plan.settings.gateway}" if plan.settings.gateway else "")
                    + ".",
                    "Settings.Update + Device.Reapply ok; IP4Config shows the address",
                )
            time.sleep(0.5)
        return finish(
            OperationState.PARTIAL,
            f"The fixed address is saved for {name} but the adapter does not show it yet.",
            f"profile ok; IP4Config lacks {want}",
            "Refresh Network in a moment; reconnect the adapter if it stays missing.",
            succeeded=("address saved in the profile",),
            failed=("address applied to the adapter",),
        )
    if plan.verb == "auto":
        if method != "auto":
            return finish(
                OperationState.FAILED, f"The profile for {name} is still set to '{method}'."
            )
        fresh = _fresh_device(bus, plan)
        state = fresh.link_state if fresh else "gone"
        return finish(
            OperationState.VERIFIED,
            f"{name} is set to get its address automatically (adapter: {state}).",
            "Settings.Update + Device.Reapply ok; method=auto",
        )
    want_dns = list(plan.dns) if plan.verb == "dns" else []
    if dns != want_dns:
        return finish(
            OperationState.FAILED,
            f"The DNS setting for {name} did not take.",
            f"dns={dns} wanted={want_dns}",
        )
    return finish(
        OperationState.VERIFIED,
        f"{name} DNS: {', '.join(dns) if dns else 'from the network'}.",
        "Settings.Update + Device.Reapply ok; dns re-read",
    )
