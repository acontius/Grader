"""
Shared fixtures for the Task 1 Grader Agent test suite.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Helper – build a submission on disk
# ---------------------------------------------------------------------------

def write_submission(
    root: Path,
    n_docs: int = 12,
    n_questions: int = 10,
    *,
    include_pii: bool = False,
    short_docs: bool = False,
    duplicate_files: bool = False,
    bad_url: bool = False,
    bad_date: bool = False,
    missing_field: Optional[str] = None,
    invalid_doc_id_in_q: bool = False,
    doc_types: Optional[List[str]] = None,
    extra_files: Optional[List[str]] = None,
) -> Path:
    """
    Create a complete submission directory under `root`.
    Returns the root path.
    """
    docs_dir = root / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    if doc_types is None:
        doc_types = ["advisory", "incident_report", "technical_doc", "case_study"]

    metadata: List[Dict[str, Any]] = []
    questions: List[Dict[str, Any]] = []

    for i in range(1, n_docs + 1):
        doc_id = f"doc{i:02d}"
        content = f"Short {doc_id}." if short_docs else (f"This is sample document {doc_id}. " * 15)
        if include_pii and i == 1:
            content += " Contact: alice@example.com phone 555-123-4567 "

        (docs_dir / f"{doc_id}.txt").write_text(content, encoding="utf-8")

        entry: Dict[str, Any] = {
            "doc_id": doc_id,
            "title": f"Title for {doc_id}",
            "source_url": f"https://example.com/{doc_id}",
            "license": "Public Domain",
            "date": "2024-01-15",
            "doc_type": doc_types[(i - 1) % len(doc_types)],
            "language": "en",
            "is_synthetic": True,
        }

        if bad_url and i == 1:
            entry["source_url"] = "not-a-valid-url"
        if bad_date and i == 1:
            entry["date"] = "15/01/2024"
        if missing_field and i == 1:
            entry.pop(missing_field, None)

        metadata.append(entry)

    # Optional duplicate content
    if duplicate_files and n_docs >= 2:
        src = docs_dir / "doc01.txt"
        dst = docs_dir / "doc02.txt"
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    # Extra non-supported files (should be ignored)
    if extra_files:
        for name in extra_files:
            (docs_dir / name).write_text("ignored content", encoding="utf-8")

    for i in range(1, n_questions + 1):
        doc_id = f"doc{((i - 1) % max(n_docs, 1)) + 1:02d}"
        q: Dict[str, Any] = {
            "question_id": f"q{i:02d}",
            "question": f"What is the main topic of document {doc_id}?",
            "answer": f"Sample answer for question {i}.",
            "doc_id": doc_id if not (invalid_doc_id_in_q and i == 1) else "nonexistent",
        }
        questions.append(q)

    (root / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (root / "questions.json").write_text(
        json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return root


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_submission(tmp_path: Path):
    """Factory fixture – call with kwargs to customise the submission."""

    def _factory(**kwargs) -> Path:
        return write_submission(tmp_path / "sub", **kwargs)

    return _factory


@pytest.fixture
def perfect_submission(tmp_path: Path) -> Path:
    """30 docs + 12 questions – should score (near) 100."""
    return write_submission(tmp_path / "perfect", n_docs=30, n_questions=12)


@pytest.fixture
def minimal_valid_submission(tmp_path: Path) -> Path:
    """Just enough to pass basic structure checks."""
    return write_submission(tmp_path / "minimal", n_docs=12, n_questions=10)
