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
"""Network Connections data from NetworkManager over D-Bus, read-only.

INVARIANT: link state, connection profile, IP configuration, DNS, gateway,
connectivity check, and Internet reachability are reported as separate facts
and never collapsed into one Connected flag (TB-INV-071, TB-INV-149).
Unknown layers stay Unknown. Identity for later mutation is the connection
UUID plus the device interface (TB-INV-052), captured here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.identity import ConnectionIdentity
from .bus import Bus

NM = "org.freedesktop.NetworkManager"
NM_PATH = "/org/freedesktop/NetworkManager"

DEVICE_TYPES = {
    1: "Ethernet",
    2: "Wi-Fi",
    5: "Bluetooth",
    6: "OLPC mesh",
    7: "WiMAX",
    8: "Modem",
    9: "InfiniBand",
    10: "Bond",
    11: "VLAN",
    12: "ADSL",
    13: "Bridge",
    14: "Generic",
    15: "Team",
    16: "TUN",
    17: "IP tunnel",
    18: "MACVLAN",
    19: "VXLAN",
    20: "Veth",
    21: "MACsec",
    22: "Dummy",
    23: "PPP",
    24: "Open vSwitch interface",
    25: "Open vSwitch port",
    26: "Open vSwitch bridge",
    27: "WPAN",
    28: "6LoWPAN",
    29: "WireGuard",
    30: "Wi-Fi P2P",
    31: "VRF",
    32: "Loopback",
}

DEVICE_STATES = {
    0: "Unknown",
    10: "Unmanaged",
    20: "Unavailable",
    30: "Disconnected",
    40: "Preparing",
    50: "Configuring",
    60: "Needs authentication",
    70: "Getting IP address",
    80: "Checking IP",
    90: "Waiting for other connections",
    100: "Connected",
    110: "Deactivating",
    120: "Failed",
}

CONNECTIVITY = {
    0: "Unknown",
    1: "No connectivity",
    2: "Portal (sign-in page)",
    3: "Limited",
    4: "Full Internet access",
}

NM_STATES = {
    0: "Unknown",
    10: "Networking off",
    20: "Disconnected",
    30: "Disconnecting",
    40: "Connecting",
    50: "Connected (local)",
    60: "Connected (site)",
    70: "Connected (global)",
}


@dataclass(frozen=True)
class NetworkDevice:
    interface: str
    kind: str  # DEVICE_TYPES name or "Unknown"
    link_state: str  # DEVICE_STATES name
    managed: bool | None
    driver: str
    mac: str
    connection_name: str  # active profile, "" if none
    connection_uuid: str
    identity: ConnectionIdentity | None
    ipv4: tuple[str, ...]  # "addr/prefix"
    ipv6: tuple[str, ...]
    gateway4: str
    dns: tuple[str, ...]
    object_path: str

    @property
    def is_loopback(self) -> bool:
        return self.kind == "Loopback"


@dataclass(frozen=True)
class NetworkOverview:
    available: bool
    detail: str
    backend_version: str = ""
    overall_state: str = "Unknown"
    connectivity: str = "Unknown"  # the connectivity *check* result, not a claim
    devices: tuple[NetworkDevice, ...] = field(default_factory=tuple)


def _addr_list(data: Any) -> tuple[str, ...]:
    out = []
    for entry in data or []:
        try:
            addr = entry.get("address", "")
            prefix = entry.get("prefix", "")
            out.append(f"{addr}/{prefix}" if prefix != "" else str(addr))
        except AttributeError:
            continue
    return tuple(out)


def _ns_list(data: Any) -> tuple[str, ...]:
    out = []
    for entry in data or []:
        try:
            out.append(str(entry.get("address", "")))
        except AttributeError:
            continue
    return tuple(x for x in out if x)


def read_network(bus: Bus | None = None) -> NetworkOverview:
    bus = bus or Bus.system()
    if bus.conn is None:
        return NetworkOverview(False, f"The system bus is not reachable: {bus.error}")
    if NM not in bus.names() and NM not in bus.activatable():
        return NetworkOverview(False, "NetworkManager is not present on this computer.")
    top = bus.properties(NM, NM_PATH, NM)
    if not top:
        return NetworkOverview(False, "NetworkManager did not answer.")
    devices: list[NetworkDevice] = []
    for dpath in top.get("Devices", []):
        d = bus.properties(NM, dpath, f"{NM}.Device")
        if not d:
            continue
        kind = DEVICE_TYPES.get(int(d.get("DeviceType", 0)), "Unknown")
        mac = ""
        for sub in ("Wired", "Wireless"):
            v, err = bus.property(NM, dpath, f"{NM}.Device.{sub}", "HwAddress")
            if not err and v:
                mac = str(v)
                break
        conn_name = conn_uuid = ""
        identity = None
        ac_path = d.get("ActiveConnection", "/")
        if ac_path and ac_path != "/":
            ac = bus.properties(NM, ac_path, f"{NM}.Connection.Active")
            conn_name = str(ac.get("Id", ""))
            conn_uuid = str(ac.get("Uuid", ""))
            if conn_uuid:
                identity = ConnectionIdentity(uuid=conn_uuid, interface=str(d.get("Interface", "")))
        ipv4: tuple[str, ...] = ()
        ipv6: tuple[str, ...] = ()
        gw = ""
        dns: tuple[str, ...] = ()
        ip4_path = d.get("Ip4Config", "/")
        if ip4_path and ip4_path != "/":
            ip4 = bus.properties(NM, ip4_path, f"{NM}.IP4Config")
            ipv4 = _addr_list(ip4.get("AddressData"))
            gw = str(ip4.get("Gateway", "") or "")
            dns = _ns_list(ip4.get("NameserverData"))
        ip6_path = d.get("Ip6Config", "/")
        if ip6_path and ip6_path != "/":
            ip6 = bus.properties(NM, ip6_path, f"{NM}.IP6Config")
            ipv6 = tuple(a for a in _addr_list(ip6.get("AddressData")) if not a.startswith("fe80"))
        devices.append(
            NetworkDevice(
                interface=str(d.get("Interface", "")),
                kind=kind,
                link_state=DEVICE_STATES.get(int(d.get("State", 0)), "Unknown"),
                managed=bool(d["Managed"]) if "Managed" in d else None,
                driver=str(d.get("Driver", "")),
                mac=mac,
                connection_name=conn_name,
                connection_uuid=conn_uuid,
                identity=identity,
                ipv4=ipv4,
                ipv6=ipv6,
                gateway4=gw,
                dns=dns,
                object_path=str(dpath),
            )
        )
    return NetworkOverview(
        True,
        "Read from NetworkManager.",
        backend_version=str(top.get("Version", "")),
        overall_state=NM_STATES.get(int(top.get("State", 0)), "Unknown"),
        connectivity=CONNECTIVITY.get(int(top.get("Connectivity", 0)), "Unknown"),
        devices=tuple(devices),
    )
