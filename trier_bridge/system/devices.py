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


def read_devices(sys_root: Path = Path("/sys"), bus: Bus | None = None) -> DeviceInventory:
    devices: list[Device] = []
    sources: list[str] = []
    notes: list[str] = []
    pci_db = IdDatabase(("/usr/share/misc/pci.ids", "/usr/share/hwdata/pci.ids"))
    usb_db = IdDatabase(("/usr/share/misc/usb.ids", "/usr/share/hwdata/usb.ids"))

    pci_root = sys_root / "bus" / "pci" / "devices"
    if pci_root.is_dir():
        sources.append("/sys/bus/pci")
        for dev in sorted(pci_root.iterdir()):
            vendor = _read(dev / "vendor").replace("0x", "")
            product = _read(dev / "device").replace("0x", "")
            klass = _read(dev / "class").replace("0x", "")
            vname, pname = pci_db.name(vendor, product)
            base = PCI_CLASSES.get(int(klass[:2], 16) if klass[:2] else 0xFF, "Device")
            name = clean(f"{vname} {pname}".strip() or base)
            drv = _driver(dev)
            devices.append(
                Device(
                    category=pci_category(klass),
                    name=name,
                    bus="pci",
                    ids=f"{vendor}:{product}",
                    driver=drv,
                    working=True if drv else None,
                    sysfs_path=str(dev),
                    detail=f"{base}; PCI {dev.name}",
                )
            )
    usb_root = sys_root / "bus" / "usb" / "devices"
    if usb_root.is_dir():
        sources.append("/sys/bus/usb")
        for dev in sorted(usb_root.iterdir()):
            if ":" in dev.name or not (dev / "idVendor").exists():
                continue  # interfaces and root hubs without ids
            vendor = _read(dev / "idVendor")
            product = _read(dev / "idProduct")
            vname, pname = usb_db.name(vendor, product)
            man = clean(_read(dev / "manufacturer"))
            prod = clean(_read(dev / "product"))
            name = clean(
                f"{man or vname} {prod or pname}".strip() or f"USB device {vendor}:{product}"
            )
            cls = _read(dev / "bDeviceClass")
            drv = _driver(dev)
            devices.append(
                Device(
                    category=usb_category(cls, name),
                    name=name,
                    bus="usb",
                    ids=f"{vendor}:{product}",
                    driver=drv,
                    working=True if drv else None,
                    sysfs_path=str(dev),
                    detail=f"USB {dev.name}",
                )
            )
    seen_sysfs = {d.sysfs_path for d in devices}
    for cls, category, label in (
        ("net", Category.NETWORK, "Network adapter"),
        ("drm", Category.DISPLAY, "Display adapter"),
        ("sound", Category.AUDIO, "Sound device"),
        ("input", Category.INPUT, "Input device"),
        ("block", Category.STORAGE, "Disk"),
        ("bluetooth", Category.BLUETOOTH, "Bluetooth adapter"),
    ):
        cls_root = sys_root / "class" / cls
        if not cls_root.is_dir():
            continue
        sources.append(f"/sys/class/{cls}")
        for entry in sorted(cls_root.iterdir()):
            if cls == "drm" and ("-" in entry.name or not entry.name.startswith("card")):
                continue  # connectors and render nodes are not devices
            if cls == "block" and (entry.name.startswith("loop") or entry.name.startswith("ram")):
                continue
            if cls == "input" and not entry.name.startswith("input"):
                continue  # event/mouse nodes duplicate their parent inputN
            if cls == "net" and entry.name == "lo":
                continue
            dev_link = entry / "device"
            try:
                real = str(dev_link.resolve()) if dev_link.exists() else str(entry.resolve())
            except OSError:
                real = str(entry)
            if real in seen_sysfs:
                continue  # already listed from its PCI/USB bus entry
            seen_sysfs.add(real)
            name = clean(
                _read(entry / "name")
                or _read(entry / "device" / "modalias").split(":")[0]
                or entry.name
            )
            if cls == "input":
                name = clean(_read(entry / "name")) or entry.name
            elif cls == "block":
                model = clean(_read(entry / "device" / "model"))
                name = f"{model} ({entry.name})" if model else entry.name
            elif cls == "net":
                name = entry.name
            drv = _driver(dev_link) if dev_link.exists() else ""
            if not drv and cls == "input":
                drv = "evdev"
            devices.append(
                Device(
                    category=category,
                    name=name,
                    bus=cls,
                    ids=_read(entry / "device" / "modalias")[:40] or "",
                    driver=drv,
                    working=True if drv else None,
                    sysfs_path=real,
                    detail=f"{label}; /sys/class/{cls}/{entry.name}",
                )
            )
    vmbus = sys_root / "bus" / "vmbus" / "devices"
    if vmbus.is_dir():
        sources.append("/sys/bus/vmbus")
        for dev in sorted(vmbus.iterdir()):
            real = str(dev.resolve())
            if real in seen_sysfs:
                continue
            drv = _driver(dev)
            desc = clean(_read(dev / "device_id")) or dev.name
            devices.append(
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
    if pci_db.source:
        sources.append(pci_db.source)
    else:
        notes.append("Hardware name database (pci.ids) not found; PCI devices show IDs only.")
    if usb_db.source:
        sources.append(usb_db.source)

    bus = bus or Bus.system()
    if bus.conn is not None and "org.freedesktop.UPower" in bus.names():
        res, err = bus.call(
            "org.freedesktop.UPower",
            "/org/freedesktop/UPower",
            "org.freedesktop.UPower",
            "EnumerateDevices",
        )
        if not err and res:
            sources.append("UPower")
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
                props = bus.properties(
                    "org.freedesktop.UPower", path, "org.freedesktop.UPower.Device"
                )
                if not props:
                    continue
                kind = kinds.get(int(props.get("Type", 0)), "Power device")
                model = clean(str(props.get("Model", "")))
                pct = props.get("Percentage")
                detail = (
                    f"{kind}; charge {pct:.0f}%"
                    if isinstance(pct, float) and kind == "Battery"
                    else kind
                )
                devices.append(
                    Device(
                        category=Category.BATTERY,
                        name=model or kind,
                        bus="power",
                        ids=str(props.get("NativePath", "")),
                        driver="",
                        working=bool(props.get("IsPresent", True)),
                        sysfs_path=str(path),
                        detail=detail,
                    )
                )
    if not devices:
        notes.append("No devices could be read from this system.")
    return DeviceInventory(tuple(devices), tuple(sources), tuple(notes))
