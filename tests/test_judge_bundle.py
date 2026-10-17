"""Verify the bundle includes only intended source and detects stale copies."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.build_judge_bundle import SHARED_FILES, build_archive, check_copy, sync_copy


class JudgeBundleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in (*SHARED_FILES, "judge_submission/README.md"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture for " + relative)

    def test_archive_excludes_secrets_and_runtime_files(self):
        (self.root / ".env").write_text("SECRET_SENTINEL")
        (self.root / "backend/data/event_history.json").write_text("PRIVATE_SENTINEL")
        archive_path = build_archive(self.root / "bundle.zip", self.root)
        with ZipFile(archive_path) as archive:
            self.assertEqual(set(archive.namelist()),
                             {"ayusarthi/" + path for path in (*SHARED_FILES, "README.md", "SHA256SUMS.txt")})
            contents = b"".join(archive.read(path) for path in archive.namelist())
            self.assertNotIn(b"SECRET_SENTINEL", contents)
            self.assertNotIn(b"PRIVATE_SENTINEL", contents)

    def test_repeated_build_has_same_bytes_and_valid_manifest(self):
        first = build_archive(self.root / "first.zip", self.root)
        second = build_archive(self.root / "second.zip", self.root)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with ZipFile(first) as archive:
            for line in archive.read("ayusarthi/SHA256SUMS.txt").decode().splitlines():
                digest, name = line.split("  ", 1)
                self.assertEqual(hashlib.sha256(archive.read("ayusarthi/" + name)).hexdigest(), digest)

    def test_copy_drift_is_detected_and_sync_preserves_custom_readme(self):
        readme = (self.root / "judge_submission/README.md").read_bytes()
        sync_copy(self.root)
        self.assertEqual(check_copy(self.root), [])
        (self.root / "frontend/app.py").write_text("updated")
        self.assertEqual(check_copy(self.root), ["frontend/app.py"])
        sync_copy(self.root)
        self.assertEqual(check_copy(self.root), [])
        self.assertEqual((self.root / "judge_submission/README.md").read_bytes(), readme)

    def test_source_symlink_is_rejected(self):
        source = self.root / "frontend/app.py"
        source.unlink()
        target = self.root / "private.txt"
        target.write_text("PRIVATE_SENTINEL")
        try:
            source.symlink_to(target)
        except OSError:
            self.skipTest("Creating symlinks is unavailable on this system")
        with self.assertRaises(ValueError):
            build_archive(self.root / "bundle.zip", self.root)


if __name__ == "__main__":
    unittest.main()
