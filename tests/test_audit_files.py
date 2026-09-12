"""Behavioral checks for the portable audit helper; no installed skills touched."""

import codecs
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skill-prompt-optimizer" / "scripts" / "audit_files.py"
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("audit_files", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class AuditFilesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="skill-optimizer-tests-")
        self.base = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, relative, content=b"# Original\r\n"):
        path = self.base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def cli(self, *arguments, code=0):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, arguments)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(code, result.returncode, result.stdout + result.stderr)
        return result

    def files_list(self, *paths):
        path = self.base / "selection.json"
        path.write_text(json.dumps([str(p) for p in paths]), encoding="utf-8")
        return path

    def test_inventory_readonly_unicode_classification_and_exclusions(self):
        source = self.write("Wurzeln/öffentliche Fähigkeit/SKILL.md", "# Fähigkeit\r\n".encode())
        reference = self.write("Wurzeln/öffentliche Fähigkeit/references/Details.markdown")
        agent = self.write("Wurzeln/AGENTS.md")
        hidden = self.write("Wurzeln/.hidden/SKILL.md")
        system = self.write("Wurzeln/.system/core/SKILL.md")
        cached = self.write("Wurzeln/.codex/plugins/cache/provider/tool/SKILL.md")
        ordinary = self.write("Wurzeln/Projekt/README.md")
        for directory in AUDIT.EXCLUDED:
            self.write("Wurzeln/" + directory + "/discard/SKILL.md")
        for path in [source, reference, agent, hidden, system, cached, ordinary]:
            self.assertTrue(path.is_absolute())
        before = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in (self.base / "Wurzeln").rglob("*") if p.is_file()}
        out = self.base / "inventory.json"
        self.cli("inventory", "--root", self.base / "Wurzeln", "--out", out)
        result = json.loads(out.read_text(encoding="utf-8"))
        files = {item["path"]: item for item in result["files"]}
        self.assertEqual(7, len(files))
        self.assertEqual("skill", files[str(source)]["kind"])
        self.assertEqual("skill_reference", files[str(reference)]["kind"])
        self.assertEqual("agent_instructions", files[str(agent)]["kind"])
        self.assertEqual("markdown_candidate", files[str(ordinary)]["kind"])
        self.assertFalse(files[str(hidden)]["managed"])
        self.assertTrue(files[str(system)]["managed"])
        self.assertTrue(files[str(cached)]["managed"])
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), files[str(source)]["sha256"])
        self.assertEqual(len(source.read_bytes()), files[str(source)]["bytes"])
        self.assertTrue(all("content" not in item for item in files.values()))
        self.assertEqual(len(AUDIT.EXCLUDED), len(result["skipped"]))
        after = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in (self.base / "Wurzeln").rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_explicit_managed_root_and_reference_selection(self):
        self.write("personal/SKILL.md")
        reference = self.write("personal/references/ref.md")
        managed = self.write("vendor/SKILL.md")
        out = self.base / "selected.json"
        self.cli("inventory", "--managed-root", managed.parent, "--file", reference, "--out", out)
        report = json.loads(out.read_text(encoding="utf-8"))
        files = {item["path"]: item for item in report["files"]}
        self.assertEqual(2, len(files))
        self.assertTrue(files[str(managed)]["managed"])
        self.assertEqual("skill_reference", files[str(reference)]["kind"])

    def test_inventory_requires_selection_and_reports_unknown_encoding(self):
        out = self.base / "empty.json"
        self.cli("inventory", "--out", out, code=1)
        self.assertFalse(out.exists())
        bad = self.write("unknown.md", b"\xffinvalid")
        result = self.cli("inventory", "--file", bad, "--out", out, code=1)
        report = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual("unknown", report["files"][0]["encoding"])
        self.assertEqual("decode", report["errors"][0]["operation"])
        self.assertNotIn("invalid", result.stderr)

    def test_snapshot_preserves_utf8_bom_utf16_and_exact_bytes(self):
        utf8 = self.write("Büro/utf8.md", "# Maße\r\nEnde".encode("utf-8"))
        bom = self.write("Büro/bom.md", codecs.BOM_UTF8 + b"# BOM\n")
        utf16le = self.write("Büro/le.md", codecs.BOM_UTF16_LE + "# Größe\r\n".encode("utf-16-le"))
        utf16be = self.write("Büro/be.md", codecs.BOM_UTF16_BE + "# Größe\n".encode("utf-16-be"))
        paths = [utf8, bom, utf16le, utf16be]
        run = self.base / "runs" / "first"
        self.cli("snapshot", "--files", self.files_list(*paths), "--out", run)
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(["utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"],
                         [record["encoding"] for record in manifest["files"]])
        for path, record in zip(paths, manifest["files"]):
            self.assertEqual(str(path), record["original_path"])
            self.assertEqual(path.read_bytes(), (run / record["backup"]).read_bytes())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["sha256"])

    def test_snapshot_preflight_and_existing_directory_rejection(self):
        good = self.write("good.md")
        bad = self.write("bad.md", b"\xffinvalid")
        run = self.base / "not_created"
        self.cli("snapshot", "--files", self.files_list(good, bad), "--out", run, code=1)
        self.assertFalse(run.exists())
        selection = self.files_list(good)
        self.cli("snapshot", "--files", selection, "--out", run)
        before = {p.name: p.read_bytes() for p in run.iterdir()}
        self.cli("snapshot", "--files", selection, "--out", run, code=1)
        self.assertEqual(before, {p.name: p.read_bytes() for p in run.iterdir()})

    def test_diff_actual_edits_missing_file_and_missing_final_newline(self):
        edited = self.write("edited.md", b"# Heading\nOld")
        missing = self.write("missing.md", b"# Removed\n")
        run = self.base / "run"
        self.cli("snapshot", "--files", self.files_list(edited, missing), "--out", run)
        edited.write_bytes(b"# Heading\nNew")
        missing.unlink()
        out = self.base / "changes.diff"
        result = self.cli("diff", "--run", run, "--out", out, code=1)
        text = out.read_text(encoding="utf-8")
        self.assertIn("-Old\n", text)
        self.assertIn("+New\n", text)
        self.assertIn("\\ No newline at end of file", text)
        self.assertIn("+++ /dev/null", text)
        self.assertIn("Missing current file", result.stderr)
        self.assertEqual(b"# Heading\nNew", edited.read_bytes())

    def test_diff_reports_encoding_only_change_and_backup_corruption(self):
        source = self.write("source.md", b"# Same\n")
        run = self.base / "run"
        self.cli("snapshot", "--files", self.files_list(source), "--out", run)
        source.write_bytes(codecs.BOM_UTF8 + b"# Same\n")
        out = self.base / "encoding.diff"
        self.cli("diff", "--run", run, "--out", out)
        self.assertIn("Byte-only change", out.read_text(encoding="utf-8"))
        (run / "0001.bak").write_bytes(b"tampered")
        result = self.cli("diff", "--run", run, "--out", self.base / "tampered.diff", code=1)
        self.assertIn("checksum", result.stderr)

    def test_reports_cannot_overwrite_source(self):
        source = self.write("source.md", b"# Preserve\n")
        self.cli("inventory", "--file", source, "--out", source, code=1)
        self.assertEqual(b"# Preserve\n", source.read_bytes())

    def test_symlink_not_followed_when_supported(self):
        target = self.write("outside/secret.md")
        directory = self.base / "scan"
        directory.mkdir()
        link = directory / "linked"
        try:
            link.symlink_to(target.parent, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest("Symlink creation unavailable: " + str(exc))
        out = self.base / "links.json"
        self.cli("inventory", "--root", directory, "--out", out)
        report = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual([], report["files"])
        self.assertEqual("symlink_or_reparse_point", report["skipped"][0]["reason"])

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior")
    def test_windows_junction_not_followed(self):
        target = self.write("outside-junction/secret.md")
        directory = self.base / "junction-scan"
        directory.mkdir()
        link = directory / "linked"
        environment = dict(os.environ, AUDIT_TEST_LINK=str(link), AUDIT_TEST_TARGET=str(target.parent))
        result = subprocess.run([
            "powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
            "$ErrorActionPreference = 'Stop'; New-Item -ItemType Junction -Path $env:AUDIT_TEST_LINK -Target $env:AUDIT_TEST_TARGET | Out-Null",
        ], env=environment, capture_output=True)
        if result.returncode:
            self.skipTest("Junction creation unavailable without escalation.")
        try:
            out = self.base / "junctions.json"
            self.cli("inventory", "--root", directory, "--out", out)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual([], report["files"])
            self.assertEqual("symlink_or_reparse_point", report["skipped"][0]["reason"])
            run = self.base / "unsafe-run"
            self.cli("snapshot", "--files", self.files_list(link / "secret.md"), "--out", run, code=1)
            self.assertFalse(run.exists())
        finally:
            # Remove this exact junction, never recurse into its target.
            link.rmdir()
        self.assertTrue(target.is_file())


if __name__ == "__main__":
    unittest.main()
