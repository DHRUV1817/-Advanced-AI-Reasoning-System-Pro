from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def _extract_readme_metadata_value(key: str) -> str:
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    metadata_match = re.search(r"^---\n(.*?)\n---", readme_text, re.DOTALL | re.MULTILINE)
    assert metadata_match, "README.md must include Hugging Face Space metadata"

    metadata_block = metadata_match.group(1)
    key_match = re.search(rf"^{re.escape(key)}:\s*(.+)$", metadata_block, re.MULTILINE)
    assert key_match, f"Missing '{key}' in README.md metadata"
    return key_match.group(1).strip()


def _extract_requirements_gradio_version() -> str:
    requirements_text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    version_match = re.search(r"^gradio==([^\s]+)$", requirements_text, re.MULTILINE)
    assert version_match, "requirements.txt must pin gradio to a single version"
    return version_match.group(1)


def test_huggingface_sdk_version_matches_requirements_pin():
    assert _extract_readme_metadata_value("sdk_version") == _extract_requirements_gradio_version()
