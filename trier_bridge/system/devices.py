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
"""Device Manager data from sysfs, the hardware ID databases, and UPower. Read-only.

Answers the questions a Windows user brings to Device Manager: what is this
device, is a driver bound, which driver, and is anything missing
(docs/PRODUCT-CONCEPT.md section 11.3). Hardware metadata is untrusted text
and is truncated and sanitized (TB-INV-175). Missing fields stay Unknown
(TB-INV-173). There is no Update Driver button: driver changes are not a
Trier Bridge action (TB-INV-174).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum, unique
from pathlib import Path

from .bus import Bus

PCI_CLASSES = {
    0x00: "Unclassified",
    0x01: "Storage controller",
    0x02: "Network adapter",
    0x03: "Display adapter",
    0x04: "Multimedia (audio/video)",
    0x05: "Memory controller",
    0x06: "Bridge",
    0x07: "Communication controller",
    0x08: "System peripheral",
    0x09: "Input device controller",
    0x0A: "Docking station",
    0x0B: "Processor",
    0x0C: "Serial bus controller (USB, SATA, ...)",
    0x0D: "Wireless controller",
    0x0E: "Intelligent controller",
    0x0F: "Satellite controller",
    0x10: "Encryption controller",
    0x11: "Signal processing controller",
    0x12: "Processing accelerator",
    0x13: "Non-essential instrumentation",
}

_CLEAN = re.compile(r"[\x00-\x1f\x7f]")


def clean(text: str, limit: int = 80) -> str:
    return _CLEAN.sub("", text).strip()[:limit]


@unique
class Category(Enum):
    DISPLAY = "Display adapters"
    NETWORK = "Network adapters"
    AUDIO = "Sound, video and game controllers"
    STORAGE = "Storage controllers"
    USB_CONTROLLER = "Universal Serial Bus controllers"
    USB_DEVICE = "USB devices"
    INPUT = "Keyboards, mice and input devices"
    BATTERY = "Batteries and power"
    BLUETOOTH = "Bluetooth"
    SYSTEM = "System devices"
    OTHER = "Other devices"


@dataclass(frozen=True)
class Device:
    category: Category
    name: str  # best available human name
    bus: str  # "pci", "usb", "power"
    ids: str  # "8086:1234" or "045e:0040"
    driver: str  # bound kernel driver, "" when none
    working: bool | None  # None = Unknown; True when a driver is bound (or power device present)
    sysfs_path: str
    detail: str = ""


@dataclass(frozen=True)
class DeviceInventory:
    devices: tuple[Device, ...] = field(default_factory=tuple)
    sources: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def by_category(self) -> dict[Category, list[Device]]:
        out: dict[Category, list[Device]] = {}
        for d in self.devices:
            out.setdefault(d.category, []).append(d)
        return out


class IdDatabase:
    """Parse pci.ids / usb.ids (hwdata) lazily; absent files mean names stay as IDs."""

    def __init__(self, candidates: tuple[str, ...]) -> None:
        self.vendors: dict[str, str] = {}
        self.products: dict[tuple[str, str], str] = {}
        self.source = ""
        for c in candidates:
            p = Path(c)
            if p.is_file():
                self._load(p)
                self.source = c
                break

    def _load(self, p: Path) -> None:
        vendor = ""
        try:
            with p.open("r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if not line or line.startswith("#"):
                        continue
                    if line[0] not in ("\t", " "):
                        parts = line.rstrip("\n").split("  ", 1)
                        if len(parts) == 2 and len(parts[0]) == 4:
                            vendor = parts[0].lower()
                            self.vendors[vendor] = parts[1].strip()
                        else:
                            vendor = ""
                    elif line.startswith("\t") and not line.startswith("\t\t") and vendor:
                        parts = line.strip().split("  ", 1)
                        if len(parts) == 2 and len(parts[0]) == 4:
                            self.products[(vendor, parts[0].lower())] = parts[1].strip()
        except OSError:
            pass

    def name(self, vendor: str, product: str) -> tuple[str, str]:
        v = self.vendors.get(vendor.lower(), "")
        pr = self.products.get((vendor.lower(), product.lower()), "")
        return v, pr


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _driver(dev: Path) -> str:
    try:
        return os.path.basename(os.readlink(dev / "driver"))
    except OSError:
        return ""


def pci_category(class_hex: str) -> Category:
    try:
        base = int(class_hex, 16) >> 16
    except ValueError:
        return Category.OTHER
    return {
        0x03: Category.DISPLAY,
        0x02: Category.NETWORK,
        0x04: Category.AUDIO,
        0x01: Category.STORAGE,
        0x0C: Category.USB_CONTROLLER,
        0x0D: Category.NETWORK,
        0x09: Category.INPUT,
    }.get(base, Category.SYSTEM)


def usb_category(cls: str, product: str) -> Category:
    p = product.lower()
    if cls == "09":
        return Category.USB_CONTROLLER  # hubs
    if cls == "03" or any(w in p for w in ("keyboard", "mouse", "trackpad", "touch")):
        return Category.INPUT
    if cls == "e0" or "bluetooth" in p:
        return Category.BLUETOOTH
    if cls == "01" or "audio" in p:
        return Category.AUDIO
    if cls == "08" or "storage" in p or "disk" in p:
        return Category.STORAGE
    return Category.USB_DEVICE


CLASS_PASSES: tuple[tuple[str, Category, str], ...] = (
    ("net", Category.NETWORK, "Network adapter"),
    ("drm", Category.DISPLAY, "Display adapter"),
    ("sound", Category.AUDIO, "Sound device"),
    ("input", Category.INPUT, "Input device"),
    ("block", Category.STORAGE, "Disk"),
    ("bluetooth", Category.BLUETOOTH, "Bluetooth adapter"),
)


def _pci_devices(sys_root: Path, db: IdDatabase) -> list[Device]:
    out: list[Device] = []
    root = sys_root / "bus" / "pci" / "devices"
    if not root.is_dir():
        return out
    for dev in sorted(root.iterdir()):
        vendor = _read(dev / "vendor").replace("0x", "")
        product = _read(dev / "device").replace("0x", "")
        klass = _read(dev / "class").replace("0x", "")
        vname, pname = db.name(vendor, product)
        base = PCI_CLASSES.get(int(klass[:2], 16) if klass[:2] else 0xFF, "Device")
        drv = _driver(dev)
        out.append(
            Device(
                category=pci_category(klass),
                name=clean(f"{vname} {pname}".strip() or base),
                bus="pci",
                ids=f"{vendor}:{product}",
                driver=drv,
                working=True if drv else None,
                sysfs_path=str(dev),
                detail=f"{base}; PCI {dev.name}",
            )
        )
    return out


def _usb_devices(sys_root: Path, db: IdDatabase) -> list[Device]:
    out: list[Device] = []
    root = sys_root / "bus" / "usb" / "devices"
    if not root.is_dir():
        return out
    for dev in sorted(root.iterdir()):
        if ":" in dev.name or not (dev / "idVendor").exists():
            continue  # interfaces and root hubs without ids
        vendor = _read(dev / "idVendor")
        product = _read(dev / "idProduct")
        vname, pname = db.name(vendor, product)
        man = clean(_read(dev / "manufacturer"))
        prod = clean(_read(dev / "product"))
        name = clean(f"{man or vname} {prod or pname}".strip() or f"USB device {vendor}:{product}")
        drv = _driver(dev)
        out.append(
            Device(
                category=usb_category(_read(dev / "bDeviceClass"), name),
                name=name,
                bus="usb",
                ids=f"{vendor}:{product}",
                driver=drv,
                working=True if drv else None,
                sysfs_path=str(dev),
                detail=f"USB {dev.name}",
            )
        )
    return out


def _class_skip(cls: str, name: str) -> bool:
    if cls == "drm":
        return "-" in name or not name.startswith("card")  # connectors, render nodes
    if cls == "block":
        return name.startswith("loop") or name.startswith("ram")
    if cls == "input":
        return not name.startswith("input")  # event/mouse nodes duplicate inputN
    return cls == "net" and name == "lo"


def _class_name(cls: str, entry: Path) -> str:
    if cls == "input":
        return clean(_read(entry / "name")) or entry.name
    if cls == "block":
        model = clean(_read(entry / "device" / "model"))
        return f"{model} ({entry.name})" if model else entry.name
    if cls == "net":
        return entry.name
    modalias = _read(entry / "device" / "modalias").split(":")[0]
    return clean(_read(entry / "name") or modalias or entry.name)


def _class_devices(sys_root: Path, seen: set[str], sources: list[str]) -> list[Device]:
    """Devices by class so bus-less guests and platform devices are still covered."""
    out: list[Device] = []
    for cls, category, label in CLASS_PASSES:
        cls_root = sys_root / "class" / cls
        if not cls_root.is_dir():
            continue
        sources.append(f"/sys/class/{cls}")
        for entry in sorted(cls_root.iterdir()):
            if _class_skip(cls, entry.name):
                continue
            dev_link = entry / "device"
            try:
                real = str(dev_link.resolve()) if dev_link.exists() else str(entry.resolve())
            except OSError:
                real = str(entry)
            if real in seen:
                continue  # already listed from its PCI/USB bus entry
            seen.add(real)
            drv = _driver(dev_link) if dev_link.exists() else ""
            if not drv and cls == "input":
                drv = "evdev"
            out.append(
                Device(
                    category=category,
                    name=_class_name(cls, entry),
                    bus=cls,
                    ids=_read(entry / "device" / "modalias")[:40] or "",
                    driver=drv,
                    working=True if drv else None,
                    sysfs_path=real,
                    detail=f"{label}; /sys/class/{cls}/{entry.name}",
                )
            )
    return out


def _vmbus_devices(sys_root: Path, seen: set[str]) -> list[Device]:
    out: list[Device] = []
    root = sys_root / "bus" / "vmbus" / "devices"
    if not root.is_dir():
        return out
    for dev in sorted(root.iterdir()):
        real = str(dev.resolve())
        if real in seen:
            continue
        drv = _driver(dev)
        desc = clean(_read(dev / "device_id")) or dev.name
        out.append(
            Device(
                category=Category.SYSTEM,
                name=f"Hyper-V {drv or 'device'}",
                bus="vmbus",
                ids=clean(_read(dev / "class_id"))[:40],
                driver=drv,
                working=True if drv else None,
                sysfs_path=real,
                detail=f"Virtual machine bus; {desc[:36]}",
            )
        )
    return out


def _power_devices(bus: Bus) -> list[Device]:
    out: list[Device] = []
    if bus.conn is None or "org.freedesktop.UPower" not in bus.names():
        return out
    res, err = bus.call(
        "org.freedesktop.UPower",
        "/org/freedesktop/UPower",
        "org.freedesktop.UPower",
        "EnumerateDevices",
    )
    if err or not res:
        return out
    kinds = {
        1: "Line power",
        2: "Battery",
        3: "UPS",
        5: "Mouse",
        6: "Keyboard",
        7: "PDA",
        8: "Phone",
    }
    for path in res[0]:
        props = bus.properties("org.freedesktop.UPower", path, "org.freedesktop.UPower.Device")
        if not props:
            continue
        kind = kinds.get(int(props.get("Type", 0)), "Power device")
        pct = props.get("Percentage")
        detail = (
            f"{kind}; charge {pct:.0f}%" if isinstance(pct, float) and kind == "Battery" else kind
        )
        out.append(
            Device(
                category=Category.BATTERY,
                name=clean(str(props.get("Model", ""))) or kind,
                bus="power",
                ids=str(props.get("NativePath", "")),
                driver="",
                working=bool(props.get("IsPresent", True)),
                sysfs_path=str(path),
                detail=detail,
            )
        )
    return out


def read_devices(sys_root: Path = Path("/sys"), bus: Bus | None = None) -> DeviceInventory:
    sources: list[str] = []
    notes: list[str] = []
    pci_db = IdDatabase(("/usr/share/misc/pci.ids", "/usr/share/hwdata/pci.ids"))
    usb_db = IdDatabase(("/usr/share/misc/usb.ids", "/usr/share/hwdata/usb.ids"))
    devices: list[Device] = []
    if (sys_root / "bus" / "pci" / "devices").is_dir():
        sources.append("/sys/bus/pci")
        devices += _pci_devices(sys_root, pci_db)
    if (sys_root / "bus" / "usb" / "devices").is_dir():
        sources.append("/sys/bus/usb")
        devices += _usb_devices(sys_root, usb_db)
    seen = {d.sysfs_path for d in devices}
    devices += _class_devices(sys_root, seen, sources)
    if (sys_root / "bus" / "vmbus" / "devices").is_dir():
        sources.append("/sys/bus/vmbus")
        devices += _vmbus_devices(sys_root, seen)
    for db in (pci_db, usb_db):
        if db.source:
            sources.append(db.source)
    if not pci_db.source:
        notes.append("Hardware name database (pci.ids) not found; PCI devices show IDs only.")
    bus = bus or Bus.system()
    power = _power_devices(bus)
    if power:
        sources.append("UPower")
    devices += power
    if not devices:
        notes.append("No devices could be read from this system.")
    return DeviceInventory(tuple(devices), tuple(sources), tuple(notes))
