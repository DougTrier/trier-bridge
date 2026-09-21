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
"""Everyday file operations as typed, confirmed, Trash-first operations (IMP-03.03).

copy, move, rename, move to Trash, create folder, remove empty folder: through
GIO, the library Files itself uses, never a shell. Nothing overwrites: an
existing destination refuses the plan. Delete means the Trash, which Files can
restore from; there is no permanent delete here (TB-INV-164). Success is
observed, not assumed: the file is where the operation says it is
(TB-INV-006). A file's identity is device and inode, revalidated right before
acting (TB-INV-050).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

from ..core.operations import Operation, OperationResult  # noqa: E402
from ..core.state import AuthorizationState, OperationState, PrivilegeClass  # noqa: E402
from ..state.journal import OperationJournal  # noqa: E402

VERBS: dict[str, tuple[str, str, str]] = {
    # verb: (button/heading, past tense, Linux equivalent)
    "copy": ("Copy", "copied", "cp"),
    "move": ("Move", "moved", "mv"),
    "rename": ("Rename", "renamed", "mv"),
    "trash": ("Move to Trash", "moved to the Trash", "gio trash"),
    "mkdir": ("Create folder", "created", "mkdir"),
    "rmdir": ("Remove empty folder", "removed", "rmdir"),
}


@dataclass(frozen=True)
class FileIdentity:
    """Device, inode, and inode change time: ext4 reuses an inode number at once when a
    file is deleted and recreated, so the number alone is not a stable identity."""

    path: str
    dev: int
    ino: int
    ctime_ns: int = 0

    @property
    def kind(self) -> str:
        return "file"

    def same_target(self, other: object) -> bool:
        return (
            isinstance(other, FileIdentity)
            and other.dev == self.dev
            and other.ino == self.ino
            and other.ctime_ns == self.ctime_ns
        )

    def label(self) -> str:
        return Path(self.path).name or self.path


def identify(path: Path) -> FileIdentity | None:
    try:
        st = path.lstat()
    except OSError:
        return None
    return FileIdentity(str(path), st.st_dev, st.st_ino, st.st_ctime_ns)


def is_still_same(identity: FileIdentity) -> bool:
    now = identify(Path(identity.path))
    return now is not None and identity.same_target(now)


@dataclass(frozen=True)
class FilePlan:
    operation: Operation
    verb: str
    source: Path
    dest: Path | None
    identity: FileIdentity | None  # None for mkdir (the folder does not exist yet)
    label: str
    preview: str

    @property
    def heading(self) -> str:
        return VERBS[self.verb][0]

    @property
    def destructive(self) -> bool:
        return self.verb in ("trash", "rmdir")


def resolve_path(cwd: Path, text: str) -> Path:
    """Windows-style separators accepted; the result is an absolute Linux path."""
    raw = text.replace("\\", "/")
    p = Path(raw)
    if not p.is_absolute():
        p = cwd / p
    return Path(os.path.normpath(str(p)))


def _refuse(
    op: Operation, state: OperationState, plain: str, next_step: str = ""
) -> OperationResult:
    return OperationResult(op.operation_id, state, plain, safest_next_step=next_step)


def plan_file(verb: str, source: str, dest: str | None, cwd: Path) -> FilePlan | OperationResult:
    """Build the typed operation, or return a terminal result explaining why not."""
    if verb not in VERBS:
        raise ValueError(f"unknown file verb {verb}")
    src = resolve_path(cwd, source)
    identity = identify(src)
    target_path: Path | None = None
    if verb in ("copy", "move"):
        if not dest:
            raise ValueError("copy and move need a destination")
        target_path = resolve_path(cwd, dest)
        if target_path.is_dir():
            target_path = target_path / src.name
    elif verb == "rename":
        if not dest:
            raise ValueError("rename needs a new name")
        new_name = dest.replace("\\", "/")
        if "/" in new_name:
            new_name = new_name.rsplit("/", 1)[1]
        target_path = src.parent / new_name
    op = Operation(
        kind=f"file.{verb}",
        target=identity or FileIdentity(str(src), 0, 0),
        privilege=PrivilegeClass.B_USER_MUTATION,
        parameters={"source": str(src), "dest": str(target_path) if target_path else ""},
    )
    name = src.name or str(src)
    if verb == "mkdir":
        if src.exists() or src.is_symlink():
            return _refuse(
                op, OperationState.UNSUPPORTED, f"{name} already exists. Nothing was changed."
            )
        if not src.parent.is_dir():
            return _refuse(
                op,
                OperationState.FAILED,
                f"The folder for {name} does not exist ({src.parent}). Nothing was changed.",
            )
        preview = f"Create the folder {name} in {src.parent}?"
        return FilePlan(op.with_preview(preview), verb, src, None, None, name, preview)
    if identity is None:
        return _refuse(
            op, OperationState.FAILED, f"The system cannot find the file specified: {source}"
        )
    if verb == "rmdir":
        if not src.is_dir():
            return _refuse(
                op, OperationState.UNSUPPORTED, f"{name} is not a folder. Nothing was changed."
            )
        if any(src.iterdir()):
            return _refuse(
                op,
                OperationState.UNSUPPORTED,
                f"{name} is not empty. Nothing was changed.",
                "Use del to move it to the Trash, where Files can restore it.",
            )
        preview = f"Remove the empty folder {name}?"
        return FilePlan(op.with_preview(preview), verb, src, None, identity, name, preview)
    if verb == "trash":
        what = "folder and everything in it" if src.is_dir() and not src.is_symlink() else "file"
        preview = (
            f"Move the {what} {name} to the Trash? Files can restore it from there; "
            "nothing is permanently deleted."
        )
        return FilePlan(op.with_preview(preview), verb, src, None, identity, name, preview)
    assert target_path is not None
    if verb == "copy" and src.is_dir() and not src.is_symlink():
        return _refuse(
            op,
            OperationState.UNSUPPORTED,
            f"{name} is a folder. Folders are copied in Files. Nothing was changed.",
        )
    if target_path.exists() or target_path.is_symlink():
        return _refuse(
            op,
            OperationState.UNSUPPORTED,
            f"{target_path.name} already exists. Nothing here overwrites; nothing was changed.",
            "Choose another name, or move the existing one to the Trash first.",
        )
    if not target_path.parent.is_dir():
        return _refuse(
            op,
            OperationState.FAILED,
            f"The destination folder does not exist ({target_path.parent}). Nothing was changed.",
        )
    if verb == "rename":
        preview = f"Rename {name} to {target_path.name}?"
    else:
        preview = f"{VERBS[verb][0]} {name} to {target_path}?"
    return FilePlan(op.with_preview(preview), verb, src, target_path, identity, name, preview)


def _classify(exc: GLib.Error) -> tuple[OperationState, str]:
    code = exc.code if exc.domain == "g-io-error-quark" else -1
    if code == Gio.IOErrorEnum.PERMISSION_DENIED:
        return OperationState.DENIED, "Linux did not allow it (permission denied)."
    if code == Gio.IOErrorEnum.NOT_FOUND:
        return OperationState.CANCELLED, "It is no longer there."
    if code == Gio.IOErrorEnum.EXISTS:
        return OperationState.FAILED, "Something with that name appeared in the meantime."
    if code == Gio.IOErrorEnum.NOT_SUPPORTED:
        return OperationState.FAILED, "This filesystem does not support it here."
    if code == Gio.IOErrorEnum.NO_SPACE:
        return OperationState.FAILED, "There is not enough space."
    return OperationState.FAILED, exc.message


def _verify(plan: FilePlan) -> bool:
    if plan.verb == "copy":
        assert plan.dest is not None
        return plan.dest.exists() and plan.source.exists()
    if plan.verb in ("move", "rename"):
        assert plan.dest is not None
        return plan.dest.exists() and not plan.source.exists() and not plan.source.is_symlink()
    if plan.verb == "trash":
        return not plan.source.exists() and not plan.source.is_symlink()
    if plan.verb == "mkdir":
        return plan.source.is_dir()
    return not plan.source.exists()


def execute_file(plan: FilePlan, journal: OperationJournal | None = None) -> OperationResult:
    op = plan.operation.with_authorization(AuthorizationState.NOT_REQUIRED)
    rec = None
    details = {"source": str(plan.source), "dest": str(plan.dest or "")}
    if plan.identity is not None:
        details.update(
            {
                "dev": str(plan.identity.dev),
                "ino": str(plan.identity.ino),
                "ctime_ns": str(plan.identity.ctime_ns),
            }
        )
    if journal is not None:
        rec = journal.open(op.operation_id, op.kind, "file", plan.label, details, plan.preview)
        journal.advance(rec, OperationState.PREVIEWED)
        journal.advance(rec, OperationState.AUTHORIZED)

    def finish(
        state: OperationState, plain: str, technical: str = "", next_step: str = ""
    ) -> OperationResult:
        if journal is not None and rec is not None:
            journal.advance(rec, state, plain, technical)
        return OperationResult(op.operation_id, state, plain, technical, next_step)

    if plan.identity is not None and not is_still_same(plan.identity):
        return finish(
            OperationState.CANCELLED,
            f"{plan.label} changed or disappeared before anything happened. Nothing was changed.",
            next_step="Look again in Files and try once more.",
        )
    if plan.dest is not None and (plan.dest.exists() or plan.dest.is_symlink()):
        return finish(
            OperationState.CANCELLED,
            f"{plan.dest.name} appeared in the meantime. Nothing here overwrites; "
            "nothing was changed.",
        )
    if journal is not None and rec is not None:
        journal.advance(rec, OperationState.EXECUTING)
    src = Gio.File.new_for_path(str(plan.source))
    try:
        if plan.verb == "copy":
            src.copy(
                Gio.File.new_for_path(str(plan.dest)), Gio.FileCopyFlags.NONE, None, None, None
            )
        elif plan.verb in ("move", "rename"):
            src.move(
                Gio.File.new_for_path(str(plan.dest)), Gio.FileCopyFlags.NONE, None, None, None
            )
        elif plan.verb == "trash":
            src.trash(None)
        elif plan.verb == "mkdir":
            src.make_directory(None)
        else:
            src.delete(None)  # rmdir: GIO refuses a non-empty directory
    except GLib.Error as exc:
        state, why = _classify(exc)
        return finish(
            state,
            f"{plan.label} could not be {VERBS[plan.verb][1]}. {why} Nothing was changed.",
            technical=f"{exc.domain} {exc.code}: {exc.message}",
        )
    if journal is not None and rec is not None:
        journal.advance(rec, OperationState.COMMITTED)
        journal.advance(rec, OperationState.VERIFYING)
    if _verify(plan):
        where = f" to {plan.dest}" if plan.verb in ("copy", "move") else ""
        if plan.verb == "rename":
            where = f" to {plan.dest.name}" if plan.dest is not None else ""
        note = " Files can restore it from the Trash." if plan.verb == "trash" else ""
        return finish(
            OperationState.VERIFIED,
            f"{plan.label} {VERBS[plan.verb][1]}{where}.{note}",
            technical=f"{VERBS[plan.verb][2]} via GIO, outcome observed",
        )
    return finish(
        OperationState.OUTCOME_UNKNOWN,
        f"The operation on {plan.label} returned, but the result could not be confirmed.",
        next_step="Check the folder in Files.",
    )
