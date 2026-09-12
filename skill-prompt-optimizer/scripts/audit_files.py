#!/usr/bin/env python3
"""Read-only Markdown inventory, byte-exact snapshots, and reviewable diffs.

Python 3.9+; standard library only. Selection is always explicit. This helper
does not rewrite or restore source files. All outputs must be new paths.
"""

import argparse
import codecs
import datetime
import difflib
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


EXCLUDED = {
    ".git", "node_modules", "venv", ".venv", "dist", "build",
    "__pycache__", ".skill-optimizer-runs",
}
AGENT_NAMES = {
    "agents.md", "agents.override.md", "claude.md", "gemini.md",
    "copilot-instructions.md",
}
MARKDOWN_SUFFIXES = {".md", ".markdown"}


def absolute(value):
    return Path(os.path.abspath(os.path.expanduser(str(value))))


def path_key(path):
    return os.path.normcase(str(path))


def is_link(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def check_no_links(path):
    """Reject links/junctions in the selected path and all existing ancestors."""
    for part in reversed((path, *path.parents)):
        try:
            if is_link(part):
                raise ValueError("Symlink or Windows reparse point: " + str(part))
        except FileNotFoundError:
            continue


def decode(data):
    """Recognize UTF-8 and BOM-marked UTF-16 without guessing legacy codecs."""
    if data.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        raise ValueError("Unsupported UTF-32 encoding; no conversion performed.")
    try:
        if data.startswith(codecs.BOM_UTF8):
            return data.decode("utf-8-sig"), "utf-8-sig"
        if data.startswith(codecs.BOM_UTF16_LE):
            return data[2:].decode("utf-16-le"), "utf-16-le"
        if data.startswith(codecs.BOM_UTF16_BE):
            return data[2:].decode("utf-16-be"), "utf-16-be"
        if b"\x00" in data:
            raise ValueError("NUL bytes: encoding is ambiguous without a UTF-16 BOM.")
        return data.decode("utf-8"), "utf-8"
    except UnicodeError as exc:
        raise ValueError("Invalid or unknown encoding; expected UTF-8 or BOM-marked UTF-16.") from exc


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_regular(path):
    check_no_links(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("Expected a regular file.")
    return path.read_bytes()


def write_new(path, data):
    check_no_links(path)
    with path.open("xb") as stream:
        stream.write(data)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def automatically_managed(path):
    parts = [part.casefold() for part in path.parts]
    return ".system" in parts or any(
        first == "plugins" and second == "cache"
        for first, second in zip(parts, parts[1:])
    )


def contains_skill(directory):
    # Probe only expected instruction names, without listing unrelated ancestors.
    for name in ("SKILL.md", "skill.md"):
        candidate = directory / name
        try:
            if not is_link(candidate) and candidate.is_file():
                return True
        except FileNotFoundError:
            continue
    return False


def inherited_skill(path, errors):
    for directory in path.parents:
        try:
            if contains_skill(directory):
                return True
        except OSError as exc:
            errors.append({"path": str(directory), "operation": "classify", "message": str(exc)})
    return False


def file_kind(path, inside_skill):
    name = path.name.casefold()
    if name == "skill.md":
        return "skill"
    if name in AGENT_NAMES or name.endswith(".instructions.md"):
        return "agent_instructions"
    return "skill_reference" if inside_skill else "markdown_candidate"


def inventory(args):
    if not (args.root or args.managed_root or args.file):
        raise ValueError("Select at least one --root, --managed-root, or --file; no defaults are scanned.")
    managed_roots = [absolute(value) for value in args.managed_root]
    root_map = {}
    for value in args.root + args.managed_root:
        path = absolute(value)
        root_map[path_key(path)] = path
    roots = list(root_map.values())
    explicit = list(dict.fromkeys(absolute(value) for value in args.file))
    result = {"schema_version": 1, "roots": [], "explicit_files": [str(p) for p in explicit],
              "errors": [], "skipped": [], "files": []}
    visited_files, visited_dirs, skipped = set(), set(), set()

    def managed(path):
        return automatically_managed(path) or any(within(path, root) for root in managed_roots)

    def skip(path, reason):
        key = (path_key(path), reason)
        if key not in skipped:
            skipped.add(key)
            result["skipped"].append({"path": str(path), "reason": reason})

    def error(path, operation, exc):
        result["errors"].append({"path": str(path), "operation": operation, "message": str(exc)})

    def excluded(path):
        if any(part.casefold() in EXCLUDED for part in path.parts):
            skip(path, "excluded_directory")
            return True
        return False

    def add_file(path, inside_skill=None):
        if path.suffix.casefold() not in MARKDOWN_SUFFIXES:
            return
        if path_key(path) in visited_files or excluded(path):
            return
        visited_files.add(path_key(path))
        try:
            if is_link(path):
                skip(path, "symlink_or_reparse_point")
                return
            data = read_regular(path)
            encoding = "unknown"
            try:
                _, encoding = decode(data)
            except ValueError as exc:
                error(path, "decode", exc)
            if inside_skill is None:
                inside_skill = inherited_skill(path, result["errors"])
            result["files"].append({
                "path": str(path), "kind": file_kind(path, inside_skill),
                "managed": managed(path), "bytes": len(data),
                "sha256": sha256(data), "encoding": encoding,
            })
        except (OSError, ValueError) as exc:
            error(path, "read", exc)

    def walk(path, inside_skill=False):
        if excluded(path) or path_key(path) in visited_dirs:
            return
        try:
            if is_link(path):
                skip(path, "symlink_or_reparse_point")
                return
            check_no_links(path)
            visited_dirs.add(path_key(path))
            with os.scandir(path) as entries:
                entries = sorted(entries, key=lambda item: item.name.casefold())
            here_skill = inside_skill or any(
                item.name.casefold() == "skill.md"
                and not is_link(Path(item.path))
                and item.is_file(follow_symlinks=False)
                for item in entries
            )
            for item in entries:
                child = Path(item.path)
                try:
                    if is_link(child):
                        skip(child, "symlink_or_reparse_point")
                    elif item.is_dir(follow_symlinks=False):
                        walk(child, here_skill)
                    elif item.is_file(follow_symlinks=False):
                        add_file(child, here_skill)
                except (OSError, ValueError) as exc:
                    error(child, "inspect", exc)
        except (OSError, ValueError) as exc:
            error(path, "scan", exc)

    for root in roots:
        result["roots"].append({"path": str(root), "managed": managed(root)})
        try:
            check_no_links(root)
            walk(root, inherited_skill(root, result["errors"]))
        except (OSError, ValueError) as exc:
            error(root, "scan", exc)
    for path in explicit:
        if path.suffix.casefold() not in MARKDOWN_SUFFIXES:
            skip(path, "not_markdown")
        else:
            add_file(path)
    result["files"].sort(key=lambda item: path_key(item["path"]))
    write_new(absolute(args.out), json_bytes(result))
    print("Inventoried {} Markdown files; {} errors; {} skipped.".format(
        len(result["files"]), len(result["errors"]), len(result["skipped"])))
    return 1 if result["errors"] else 0


def snapshot(args):
    paths = json.loads(read_regular(absolute(args.files)).decode("utf-8-sig"))
    if not isinstance(paths, list) or not paths:
        raise ValueError("--files must contain a non-empty JSON array of absolute file paths.")
    run = absolute(args.out)
    check_no_links(run)
    if run.exists():
        raise ValueError("Snapshot directory already exists: " + str(run))
    originals, seen = [], set()
    for value in paths:
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise ValueError("Each snapshot input must be an explicit absolute file path.")
        path = absolute(value)
        if path_key(path) in seen:
            raise ValueError("Duplicate snapshot input: " + str(path))
        seen.add(path_key(path))
        data = read_regular(path)
        _, encoding = decode(data)
        originals.append((path, data, encoding))
    # All source bytes and encodings have been checked before creating RUN_DIR.
    run.mkdir(parents=True, exist_ok=False)
    manifest = {"schema_version": 1,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "files": []}
    created = []
    try:
        for index, (path, data, encoding) in enumerate(originals, 1):
            backup = "{:04d}.bak".format(index)
            backup_path = run / backup
            created.append(backup_path)
            write_new(backup_path, data)
            manifest["files"].append({"original_path": str(path), "backup": backup,
                                      "sha256": sha256(data), "encoding": encoding, "bytes": len(data)})
        manifest_path = run / "manifest.json"
        created.append(manifest_path)
        write_new(manifest_path, json_bytes(manifest))
    except Exception:
        # Only remove files from this newly created run, never source files.
        for path in reversed(created):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        try:
            run.rmdir()
        except OSError:
            pass
        raise
    print("Saved {} byte-exact originals to {}".format(len(originals), run))
    return 0


def unified(original, current, original_name, current_name):
    lines = difflib.unified_diff(original.splitlines(keepends=True), current.splitlines(keepends=True),
                                 fromfile=original_name, tofile=current_name, lineterm="\n")
    chunks = []
    for line in lines:
        chunks.append(line)
        if not line.endswith("\n"):
            chunks.append("\n\\ No newline at end of file\n")
    return "".join(chunks)


def diff(args):
    run = absolute(args.run)
    manifest = json.loads(read_regular(run / "manifest.json").decode("utf-8-sig"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or not isinstance(manifest.get("files"), list):
        raise ValueError("Invalid snapshot manifest.")
    chunks, problems, changed = [], [], 0
    for record in manifest["files"]:
        if not isinstance(record, dict):
            raise ValueError("Invalid snapshot manifest entry.")
        backup = record.get("backup", "")
        original_path = record.get("original_path", "")
        if (not isinstance(backup, str) or Path(backup).name != backup
                or Path(backup).suffix != ".bak" or not Path(backup).stem.isdigit()
                or not isinstance(original_path, str) or not Path(original_path).is_absolute()):
            raise ValueError("Manifest contains an invalid backup name or original path.")
        path = absolute(original_path)
        try:
            before = read_regular(run / backup)
            if sha256(before) != record.get("sha256"):
                raise ValueError("Backup checksum does not match manifest.")
            original, old_encoding = decode(before)
            missing = False
            try:
                after = read_regular(path)
                current, new_encoding = decode(after)
            except FileNotFoundError:
                current, after, new_encoding, missing = "", b"", "missing", True
                problems.append("Missing current file (shown as deletion): " + str(path))
            if before != after or missing:
                changed += 1
                chunks.append(unified(original, current, str(path) + " (snapshot)",
                                      "/dev/null" if missing else str(path) + " (current)"))
                if not missing and original == current:
                    chunks.append("# Byte-only change: {} ({} -> {}; text is unchanged)\n".format(
                        path, old_encoding, new_encoding))
        except (OSError, ValueError) as exc:
            problems.append("Cannot compare {}: {}".format(path, exc))
    write_new(absolute(args.out), "".join(chunks).encode("utf-8"))
    for problem in problems:
        print(problem, file=sys.stderr)
    print("Compared {} files; {} changed; {} problems.".format(len(manifest["files"]), changed, len(problems)))
    return 1 if problems else 0


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inventory_parser = subparsers.add_parser("inventory", help="Read selected Markdown trees; write metadata JSON.")
    inventory_parser.add_argument("--root", action="append", default=[], help="Explicit tree to scan; repeatable.")
    inventory_parser.add_argument("--managed-root", action="append", default=[], help="Explicit managed tree to scan; repeatable.")
    inventory_parser.add_argument("--file", action="append", default=[], help="Explicit Markdown file; repeatable.")
    inventory_parser.add_argument("--out", required=True, help="New JSON report path; parent must exist.")
    inventory_parser.set_defaults(handler=inventory)
    snapshot_parser = subparsers.add_parser("snapshot", help="Save exact bytes of explicitly listed files.")
    snapshot_parser.add_argument("--files", required=True, help="JSON array of absolute file paths.")
    snapshot_parser.add_argument("--out", required=True, help="New snapshot directory; existing directory is rejected.")
    snapshot_parser.set_defaults(handler=snapshot)
    diff_parser = subparsers.add_parser("diff", help="Compare snapshot originals against current files.")
    diff_parser.add_argument("--run", required=True, help="Directory containing manifest.json and backups.")
    diff_parser.add_argument("--out", required=True, help="New UTF-8 diff path; parent must exist.")
    diff_parser.set_defaults(handler=diff)
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, ValueError, TypeError) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
