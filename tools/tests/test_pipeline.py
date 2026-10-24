"""Observable filesystem and Lua behavior in disposable installs; never the live game."""
import importlib.util
import io
from contextlib import redirect_stdout
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location("pipeline", Path(__file__).resolve().parents[1] / "caretakermods.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
TEST_ROOT = p.ROOT / "artifacts/tests"
TEST_ROOT.mkdir(parents=True, exist_ok=True)


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=TEST_ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.game = self.root / "game"
        self.game.mkdir()
        self.output = self.root / "build"
        (self.output / "scripts").mkdir(parents=True)
        (self.output / "scripts/main.lua").write_text('print("one")')
        (self.output / "enabled.txt").write_bytes(b"")
        self.mod = {"id": "sample", "folder": "Sample"}
        self.target = self.game / p.BINARY / "ue4ss/Mods/Sample"
        self.stopped = patch.object(p, "require_stopped")
        self.stopped.start()
        self.addCleanup(self.stopped.stop)

    def deploy(self, **kwargs):
        return p.deploy_files(self.mod, self.output, "source-one", self.game, self.root, **kwargs)

    def test_dry_run_never_creates_game_files(self):
        self.assertEqual(self.deploy(dry_run=True), "pending")
        self.assertEqual(list(self.game.rglob("*")), [])

    def test_repeat_update_backup_and_unrelated_file_preservation(self):
        shared = self.game / p.BINARY / "ue4ss/Mods/mods.txt"
        shared.parent.mkdir(parents=True)
        shared.write_text("Other : 1\n")
        self.assertEqual(self.deploy(), "deployed")
        self.assertEqual(self.deploy(), "current")
        config = self.target / "user-settings.json"
        config.write_text("personal config")
        (self.output / "scripts/main.lua").write_text('print("two")')
        self.assertEqual(self.deploy(), "deployed")
        self.assertEqual((self.target / "scripts/main.lua").read_text(), 'print("two")')
        self.assertEqual(shared.read_text(), "Other : 1\n")
        self.assertEqual(config.read_text(), "personal config")
        backups = [f.read_bytes() for f in (self.root / "artifacts/backups").rglob("*") if f.is_file()]
        self.assertIn(b'print("one")', backups)

    def test_unmanaged_directory_is_refused(self):
        self.target.mkdir(parents=True)
        (self.target / "mine.lua").write_text("do not touch")
        with self.assertRaisesRegex(ValueError, "Unmanaged"):
            self.deploy()
        self.assertFalse((self.target / "enabled.txt").exists())

    def test_manifest_ownership_conflict(self):
        self.deploy()
        manifest = p.read_json(self.target / p.INSTALL)
        manifest["id"] = "someone-else"
        p.write_json(self.target / p.INSTALL, manifest)
        with self.assertRaisesRegex(ValueError, "ownership"):
            self.deploy()

    def test_modified_installed_source_is_preserved(self):
        self.deploy()
        (self.target / "scripts/main.lua").write_text("personal edits")
        with self.assertRaisesRegex(ValueError, "edited externally"):
            self.deploy()
        self.assertEqual((self.target / "scripts/main.lua").read_text(), "personal edits")

    def test_obsolete_files_are_not_silently_deleted(self):
        self.deploy()
        (self.output / "scripts/main.lua").unlink()
        with self.assertRaisesRegex(ValueError, "Obsolete"):
            self.deploy()
        self.assertTrue((self.target / "scripts/main.lua").exists())

    def test_running_game_refuses_writes(self):
        with patch.object(p, "require_stopped", side_effect=ValueError("game running")):
            with self.assertRaisesRegex(ValueError, "running"):
                self.deploy()
        self.assertFalse(self.target.exists())

    def test_mid_transaction_failure_rolls_back_prior_files(self):
        self.deploy()
        before = {f.relative_to(self.target): f.read_bytes() for f in self.target.rglob("*") if f.is_file()}
        (self.output / "scripts/main.lua").write_text("version two")
        real_copy = p.shutil.copy2

        def fail_manifest(src, dst):
            if Path(src).suffix == ".json":
                raise OSError("fixture copy failure")
            return real_copy(src, dst)

        with patch.object(p.shutil, "copy2", side_effect=fail_manifest):
            with self.assertRaisesRegex(OSError, "fixture"):
                self.deploy()
        after = {f.relative_to(self.target): f.read_bytes() for f in self.target.rglob("*") if f.is_file()}
        self.assertEqual(before, after)

    def test_hash_failure_preserves_prior_install(self):
        self.deploy()
        (self.output / "scripts/main.lua").write_text("version two")
        real_digest = p.digest
        with patch.object(p, "digest", side_effect=lambda f: "corrupt" if Path(f).suffix == ".tmp" else real_digest(f)):
            with self.assertRaisesRegex(ValueError, "Staged hash"):
                self.deploy()
        self.assertEqual((self.target / "scripts/main.lua").read_text(), 'print("one")')
        self.assertFalse(list(self.target.rglob("*.tmp")))

    def test_lock_serializes_pipeline(self):
        with p.pipeline_lock(self.root):
            with self.assertRaisesRegex(ValueError, "Another pipeline"):
                with p.pipeline_lock(self.root):
                    self.fail("second owner")
        self.assertFalse((self.root / ".cache/pipeline.lock").exists())

    def test_path_escape_is_refused(self):
        with self.assertRaisesRegex(ValueError, "remain inside"):
            p.within(self.game, self.game / "../outside.lua")

    def test_loader_conflict_is_preflighted_before_copying(self):
        source = self.root / ".tools/ue4ss"
        (source / "ue4ss").mkdir(parents=True)
        (source / "ue4ss/UE4SS.dll").write_bytes(b"fixture loader")
        (source / "dwmapi.dll").write_bytes(b"fixture proxy")
        files = {f.relative_to(source).as_posix(): p.digest(f) for f in source.rglob("*") if f.is_file()}
        fixture_hash = p.digest(source / "ue4ss/UE4SS.dll")
        p.write_json(self.root / ".tools/loader-provenance.json", {"dllSha256": fixture_hash, "files": files})
        proxy = self.game / p.BINARY / "dwmapi.dll"
        proxy.parent.mkdir(parents=True)
        proxy.write_bytes(b"existing other loader")
        with patch.object(p, "LOADER_HASH", fixture_hash):
            with self.assertRaisesRegex(ValueError, "different loader"):
                p.loader_plan(self.game, self.root)
        self.assertFalse((self.game / p.BINARY / "ue4ss").exists())

    def test_archive_escape_is_refused_before_extraction(self):
        archive = self.root / "bad.zip"
        with zipfile.ZipFile(archive, "w") as target:
            target.writestr("safe.txt", "safe")
            target.writestr("../escape.txt", "unsafe")
        destination = self.root / "extract"
        with self.assertRaisesRegex(ValueError, "Unsafe archive"):
            p.extract_verified(archive, p.digest(archive), destination)
        self.assertFalse(destination.exists())

    def test_wrong_archive_hash_is_refused(self):
        archive = self.root / "bad.zip"
        archive.write_bytes(b"not even a zip")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            p.extract_verified(archive, "0" * 64, self.root / "extract")


class SourceAndLuaTests(unittest.TestCase):
    def test_dirty_source_refuses_deployment(self):
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as tmp:
            root = Path(tmp)
            p.run(["git", "init", "-q", root])
            (root / "source.lua").write_text("original")
            p.run(["git", "add", "source.lua"], cwd=root)
            p.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"], cwd=root)
            p.require_committed(root)
            (root / "source.lua").write_text("changed")
            with self.assertRaisesRegex(ValueError, "Commit source"):
                p.require_committed(root)

    def test_process_detection_blocks_running_shipping_exe(self):
        with patch.object(p, "run", return_value=subprocess.CompletedProcess([], 0, f'"{p.EXE}","1234"')):
            with self.assertRaisesRegex(ValueError, "running"):
                p.require_stopped()

    def test_process_detection_fails_closed(self):
        with patch.object(p, "run", side_effect=subprocess.CalledProcessError(1, "tasklist")):
            with self.assertRaises(subprocess.CalledProcessError):
                p.require_stopped()

    def test_probe_ready_and_missing_api_fallback(self):
        source = (p.ROOT / "mods/DevProbe/scripts/main.lua").read_text()
        for available in (True, False):
            lua = p.lua_runtime()
            logs = []
            lua.globals().print = logs.append
            if available:
                lua.execute("function RegisterHook() error('probe must not install hooks') end")
            lua.execute(source)
            text = "".join(logs)
            self.assertIn("[Caretaker.DevProbe] init", text)
            self.assertIn("ready:" if available else "fallback:", text)
            self.assertNotIn("failed:" if available else "ready:", text)

    def test_invalid_lua_fails_build(self):
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as tmp:
            root = Path(tmp)
            folder = root / "mods/Sample"
            (folder / "scripts").mkdir(parents=True)
            (folder / "scripts/main.lua").write_text("local = invalid!")
            (folder / "README.md").write_text("fixture")
            (root / "caretakermods.json").write_text("{}")
            (root / "deploy.ps1").write_text("fixture")
            with patch.object(p, "lua_runtime", return_value=p.lua_runtime()):
                with self.assertRaises(Exception):
                    p.build({"id": "sample", "folder": "Sample"}, root)
            self.assertFalse(list((root / "artifacts").rglob("enabled.txt")))

    def test_package_has_only_expected_payload(self):
        mod = p.registry()[0]
        with redirect_stdout(io.StringIO()):
            p.package(mod)
        with zipfile.ZipFile(p.ROOT / "artifacts/packages/dev-probe.zip") as archive:
            self.assertEqual(set(archive.namelist()), {
                "ue4ss/Mods/DevProbe/scripts/main.lua", "ue4ss/Mods/DevProbe/enabled.txt", "ue4ss/Mods/DevProbe/README.md"})


if __name__ == "__main__":
    unittest.main()
