"""
Automated tests for the Task 1 Grader Agent.
Run: pytest tests/ -v
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from grader import (
    DocumentChecker, Grader, MetadataChecker, QuestionChecker,
    compute_file_hash, extract_text, is_iso_date, is_valid_url,
)
from tests.conftest import write_submission


class TestHelpers:
    def test_valid_url(self):
        assert is_valid_url("https://example.com/path") is True
        assert is_valid_url("ftp://x.com") is False
        assert is_valid_url("") is False

    def test_iso_date(self):
        assert is_iso_date("2024-01-15") is True
        assert is_iso_date("15-01-2024") is False
        assert is_iso_date("2024-13-01") is False

    def test_hash_deterministic(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("hello")
        assert compute_file_hash(f) == compute_file_hash(f)
        assert len(compute_file_hash(f)) == 64


class TestDocumentChecker:
    def test_extensions(self, tmp_path):
        (tmp_path / "a.txt").write_text("x" * 60)
        (tmp_path / "b.pdf").write_text("%PDF")
        (tmp_path / "ignore.md").write_text("x")
        c = DocumentChecker(tmp_path)
        stems = {p.stem for p in c.collect_files()}
        assert stems == {"a", "b"}

    def test_duplicates(self, tmp_path):
        t = "same content " * 20
        (tmp_path / "d1.txt").write_text(t)
        (tmp_path / "d2.txt").write_text(t)
        c = DocumentChecker(tmp_path)
        c.collect_files()
        c.compute_hashes_and_texts()
        assert len(c.find_duplicates()) == 1


class TestMetadataChecker:
    def test_valid(self):
        meta = [{
            "doc_id": "doc01", "title": "T", "source_url": "https://example.com",
            "license": "PD", "date": "2024-01-01", "doc_type": "advisory",
            "language": "en", "is_synthetic": False,
        }]
        c = MetadataChecker(meta, {"doc01"})
        valid, total = c.validate()
        assert valid == 1 and total == 1

    def test_missing_file(self):
        meta = [{
            "doc_id": "missing", "title": "T", "source_url": "https://example.com",
            "license": "PD", "date": "2024-01-01", "doc_type": "advisory",
            "language": "en", "is_synthetic": False,
        }]
        c = MetadataChecker(meta, set())
        valid, _ = c.validate()
        assert valid == 0


class TestQuestionChecker:
    def test_valid(self):
        qs = [{"question_id": "q01", "question": "What?", "answer": "This.", "doc_id": "doc01"}]
        c = QuestionChecker(qs, {"doc01"})
        valid, total = c.validate()
        assert valid == 1


class TestGraderScoring:
    def test_perfect(self, perfect_submission):
        r = Grader(perfect_submission).grade()
        assert r.total_score >= 95
        assert r.breakdown["document_count"]["score"] == 30
        assert r.errors == []

    def test_too_few_docs(self, tmp_submission):
        root = tmp_submission(n_docs=8, n_questions=10)
        r = Grader(root).grade()
        assert r.breakdown["document_count"]["score"] == 0

    def test_linear_scaling(self, tmp_submission):
        root = tmp_submission(n_docs=20, n_questions=10)
        r = Grader(root).grade()
        assert r.breakdown["document_count"]["score"] == 15

    def test_duplicate_penalty(self, tmp_submission):
        root = tmp_submission(n_docs=30, n_questions=10, duplicate_files=True)
        r = Grader(root).grade()
        assert r.breakdown["document_count"]["score"] == 25

    def test_missing_metadata(self, tmp_path):
        root = tmp_path / "sub"
        (root / "documents").mkdir(parents=True)
        (root / "documents" / "doc01.txt").write_text("hello world " * 20)
        (root / "questions.json").write_text("[]")
        r = Grader(root).grade()
        assert r.total_score == 0
        assert any("metadata.json" in e for e in r.errors)

    def test_bad_url(self, tmp_submission):
        root = tmp_submission(n_docs=12, n_questions=10, bad_url=True)
        r = Grader(root).grade()
        assert r.breakdown["metadata_completeness"]["valid"] == 11

    def test_pii_deduction(self, tmp_submission):
        root = tmp_submission(n_docs=12, n_questions=10, include_pii=True)
        r = Grader(root).grade()
        assert r.breakdown["data_hygiene"]["score"] <= 5

    def test_report_structure(self, perfect_submission):
        d = Grader(perfect_submission).grade().to_dict()
        assert "total_score" in d and "breakdown" in d
        for k in ("document_count", "metadata_completeness", "question_set", "data_hygiene"):
            assert k in d["breakdown"]


class TestCLI:
    def test_cli_json(self, perfect_submission, tmp_path):
        import subprocess
        out = tmp_path / "report.json"
        result = subprocess.run(
            [sys.executable, str(ROOT / "grader.py"),
             "--submission", str(perfect_submission), "--output", str(out)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(out.read_text())
        assert data["total_score"] >= 95
