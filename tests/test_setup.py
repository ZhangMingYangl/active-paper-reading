import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SETUP = REPO / "setup.py"
TEMPLATE = "论文阅读-主动思考模板.md"
TEST_TEMP_ROOT = REPO / ".test-tmp"
TEST_TEMP_ROOT.mkdir(exist_ok=True)


class SetupIntegrationTests(unittest.TestCase):
    def make_vault(self, root, templates_folder=None):
        vault = root / "vault"
        obsidian = vault / ".obsidian"
        obsidian.mkdir(parents=True)
        if templates_folder is not None:
            (obsidian / "templates.json").write_text(
                json.dumps({"folder": templates_folder}, ensure_ascii=False), encoding="utf-8"
            )
        return vault

    def run_setup(self, vault, *args):
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        return subprocess.run(
            [sys.executable, str(SETUP), "--vault", str(vault), *args],
            cwd=REPO,
            env=env,
            text=True,
            encoding="utf-8",
            capture_output=True,
        )

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as tmp:
            root = Path(tmp)
            vault = self.make_vault(root)
            result = self.run_setup(vault, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((vault / "论文阅读").exists())
            self.assertEqual(list((vault / ".obsidian").iterdir()), [])

    def test_fresh_install_configures_templates(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as tmp:
            vault = self.make_vault(Path(tmp))
            result = self.run_setup(vault)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((vault / "论文阅读" / "templates" / TEMPLATE).is_file())
            plugins = json.loads((vault / ".obsidian" / "core-plugins.json").read_text(encoding="utf-8"))
            settings = json.loads((vault / ".obsidian" / "templates.json").read_text(encoding="utf-8"))
            self.assertIn("templates", plugins)
            self.assertEqual(settings["folder"], "论文阅读/templates")

    def test_update_keeps_two_modified_same_name_backups(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as tmp:
            vault = self.make_vault(Path(tmp), "我的模板")
            install = self.run_setup(vault)
            self.assertEqual(install.returncode, 0, install.stderr)

            installed = vault / "论文阅读" / "templates" / TEMPLATE
            extra = vault / "我的模板" / TEMPLATE
            installed.write_text("DIST_INSTALLED\n" + installed.read_text(encoding="utf-8"), encoding="utf-8")
            extra.write_text("DIST_EXTRA\n" + extra.read_text(encoding="utf-8"), encoding="utf-8")

            update = self.run_setup(vault, "--update")
            self.assertEqual(update.returncode, 0, update.stderr)
            backups = list((vault / "论文阅读" / "备份").rglob("*.md"))
            self.assertEqual(len(backups), 2)
            contents = [path.read_text(encoding="utf-8") for path in backups]
            self.assertTrue(any("DIST_INSTALLED" in content for content in contents))
            self.assertTrue(any("DIST_EXTRA" in content for content in contents))

    def test_folder_cannot_escape_vault(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as tmp:
            root = Path(tmp)
            vault = self.make_vault(root)
            outside = root / "outside"
            result = self.run_setup(vault, "--folder", "../outside")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(outside.exists())

    def test_configured_template_folder_cannot_escape_vault(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as tmp:
            root = Path(tmp)
            vault = self.make_vault(root, "../outside")
            outside = root / "outside"
            result = self.run_setup(vault)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(outside.exists())
            self.assertFalse((vault / "论文阅读").exists())

    def test_invalid_obsidian_json_stops_before_copy(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as tmp:
            vault = self.make_vault(Path(tmp))
            (vault / ".obsidian" / "core-plugins.json").write_text("{broken", encoding="utf-8")
            result = self.run_setup(vault)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((vault / "论文阅读").exists())

    def test_manifest_extra_template_cannot_escape_vault(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as tmp:
            root = Path(tmp)
            vault = self.make_vault(root)
            install = self.run_setup(vault)
            self.assertEqual(install.returncode, 0, install.stderr)
            manifest = vault / "论文阅读" / ".apr-install.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["extra_template"] = {"path": "../outside/escape.md", "hash": "invalid"}
            manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = self.run_setup(vault, "--update")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "outside").exists())


if __name__ == "__main__":
    unittest.main()
