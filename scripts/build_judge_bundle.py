"""Build a review archive from an explicit list of canonical source files."""
import argparse
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
SHARED_FILES = (
    ".env.example", ".gitignore", ".streamlit/config.toml", "requirements.txt", "requirements-voice.txt",
    "constraints-demo.txt", "SECURITY.md",
    "backend/__init__.py", "backend/monitor.py", "backend/event_detector.py",
    "backend/event_store.py", "backend/tool_server.py", "backend/voice.py",
    "backend/requirements.txt", "backend/data/README.md",
    "backend/data/calibration.json", "backend/data/profile_demo.json",
    "backend/data/health_notes.json", "frontend/__init__.py", "frontend/app.py",
    "frontend/ayusarthi_logo.jpeg", "frontend/requirements.txt",
    "docs/ARCHITECTURE.md", "prompts/agent_system_prompt.txt",
)


def source_bytes(root, relative):
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Package source must remain inside the repository: {relative}")
    return path.read_bytes()


def check_copy(root=ROOT):
    mismatches = []
    for relative in SHARED_FILES:
        expected = source_bytes(root, relative)
        target = root / "judge_submission" / relative
        if (not target.is_file() or target.is_symlink()
                or not target.resolve().is_relative_to(root.resolve() / "judge_submission")
                or target.read_bytes() != expected):
            mismatches.append(relative)
    return mismatches


def sync_copy(root=ROOT):
    for relative in SHARED_FILES:
        content = source_bytes(root, relative)
        target = root / "judge_submission" / relative
        if target.is_symlink() or not target.resolve().is_relative_to(root.resolve() / "judge_submission"):
            raise ValueError(f"Judge destination must remain inside the package: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def build_archive(output, root=ROOT):
    files = {name: source_bytes(root, name) for name in SHARED_FILES}
    files["README.md"] = source_bytes(root, "judge_submission/README.md")
    manifest = "".join(f"{hashlib.sha256(content).hexdigest()}  {name}\n"
                       for name, content in sorted(files.items()))
    files["SHA256SUMS.txt"] = manifest.encode("utf-8")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(files.items()):
            # Stable ZIP metadata makes repeated builds byte-identical.
            info = ZipInfo("ayusarthi/" + name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content, compresslevel=9)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Fail if the checked-in judge copy has drifted")
    mode.add_argument("--sync", action="store_true", help="Refresh shared judge files from canonical source")
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "AYUSARTHI-judge.zip")
    args = parser.parse_args()
    if args.sync:
        sync_copy()
        print(f"Synchronized {len(SHARED_FILES)} shared files.")
    elif args.check:
        mismatches = check_copy()
        if mismatches:
            parser.exit(1, "Judge copy differs: " + ", ".join(mismatches) + "\n")
        print("Judge copy matches canonical source.")
    else:
        path = build_archive(args.output)
        print(f"Built {path}")


if __name__ == "__main__":
    main()
