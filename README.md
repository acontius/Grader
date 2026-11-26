# Task 1 Grader Agent  
**مصحح تسک ۱ – جمع‌آوری دیتاست**

A deterministic Python agent that automatically evaluates student/team submissions for the “Task 1: Dataset Collection” assignment.

---

## What the agent grades

| Category                    | Max points | What is checked |
|----------------------------|------------|-----------------|
| Document Count             | 30         | ≥ 30 valid files (`.pdf`, `.docx`, `.txt`). Linear scale between 10–30. Duplicates → –5 |
| Metadata Completeness      | 30         | All required fields present & valid, `doc_id` matches a real file, URL & ISO date correct |
| Question Set Quality       | 30         | ≥ 10 questions, each with non-empty question/answer/`doc_id` that exists in metadata |
| Data Hygiene & Quality     | 10         | No obvious PII, documents readable (≥ 50 chars), ≥ 3 distinct `doc_type`s |
| **Total**                  | **100**    | |

---

## Expected submission structure

```
submission/
├── documents/          # PDF, DOCX or TXT files
│   ├── doc1.pdf
│   ├── doc2.docx
│   └── …
├── metadata.json       # array of document objects
└── questions.json      # array of question objects (≥ 10)
```

### Required metadata fields
`doc_id`, `title`, `source_url`, `license`, `date` (YYYY-MM-DD), `doc_type`, `language`, `is_synthetic` (bool)

### Required question fields
`question_id`, `question`, `answer`, `doc_id` (must exist in metadata)

---

## Installation

```bash
cd task1-grader-agent
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Usage

```bash
python grader.py --submission path/to/submission --output report.json
```

- `--submission` (required) – path to the folder that contains `documents/`, `metadata.json` and `questions.json`
- `--output` (optional) – write the JSON report to a file (default: print to stdout)
- `--verbose` – enable debug logging

### Example with the included sample

```bash
python grader.py --submission sample_submission --output sample_report.json
cat sample_report.json
```

A well-formed sample submission (30 documents + 12 questions) is provided under `sample_submission/`. It should score close to 100.

---

## Report format

```json
{
  "total_score": 95.0,
  "breakdown": {
    "document_count": { "score": 30, "max": 30, "details": "…" },
    "metadata_completeness": { "score": 30, "max": 30, "details": "…" },
    "question_set": { "score": 30, "max": 30, "details": "…" },
    "data_hygiene": { "score": 5, "max": 10, "details": "…" }
  },
  "feedback": [
    "Document count: 30.",
    "All metadata entries are complete and valid.",
    "…"
  ],
  "errors": []
}
```

---

## Automated Testing

### Run the full suite locally

```bash
pip install -r requirements.txt
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ -v --cov=grader --cov-report=term-missing
```

### What is covered

| Area | Tests |
|------|-------|
| URL & date helpers | valid / invalid formats, edge cases |
| File hashing & text extraction | deterministic SHA-256, .txt extraction |
| DocumentChecker | extension filtering, duplicates, PII, readability |
| MetadataChecker | required fields, URL/date validation, type checks, diversity |
| QuestionChecker | required fields, missing doc_id, duplicates |
| Full Grader scoring | perfect submission, linear scaling, penalties (duplicates, PII, short docs, low diversity), missing files, bad JSON |
| CLI | end-to-end subprocess smoke test producing valid JSON |

### Continuous Integration

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs the suite on Python 3.9–3.12 on every push/PR and also grades the included sample submission as a smoke test.

---

## Design notes

- **Modular** – separate classes for structure validation, document inspection, metadata checking, question checking and final scoring.
- **Robust** – missing files, invalid JSON, unreadable PDFs, etc. are reported in the `errors` / `feedback` lists; the process never crashes.
- **Deterministic** – no external network calls (URL validation is pure regex/parsing), no random behaviour.
- **Safe** – the agent only reads files; it never executes code from the submission.
- Supports `.txt`, `.pdf` (via `pypdf`) and `.docx` (via `python-docx`).

---

## Project layout

```
task1-grader-agent/
├── grader.py                 # main CLI & grading logic
├── requirements.txt
├── README.md
├── pytest.ini                # pytest configuration
├── .github/workflows/ci.yml  # GitHub Actions CI
├── sample_submission/
│   ├── documents/            # 30 sample .txt files
│   ├── metadata.json
│   └── questions.json
└── tests/
    ├── conftest.py           # shared fixtures
    └── test_grader.py        # unit + integration tests
```

---

## License

This grader agent itself is released under the MIT License.  
The sample documents are synthetic and free to use.
