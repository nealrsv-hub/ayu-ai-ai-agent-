"""Repository-level smoke tests for files that the prototype requires."""
from pathlib import Path
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


class RepositorySmokeTest(unittest.TestCase):
    def test_required_project_files_exist(self):
        required = [
            ROOT / "streamlit_app.py",
            ROOT / "frontend" / "app.py",
            ROOT / "frontend" / "ayusarthi_logo.jpeg",
            ROOT / "backend" / "tool_server.py",
            ROOT / "backend" / "monitor.py",
            ROOT / "backend" / "event_detector.py",
            ROOT / "automation" / "n8n" / "README.md",
            ROOT / "prompts" / "agent_system_prompt.txt",
        ]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
        self.assertEqual(missing, [], f"Missing required repository files: {missing}")

    def test_logo_is_readable_image(self):
        logo = ROOT / "frontend" / "ayusarthi_logo.jpeg"
        with Image.open(logo) as image:
            image.verify()

    def test_n8n_docs_do_not_reference_missing_setup_file(self):
        text = (ROOT / "automation" / "n8n" / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("docs/original_hackathon_setup.md", text)


if __name__ == "__main__":
    unittest.main()
