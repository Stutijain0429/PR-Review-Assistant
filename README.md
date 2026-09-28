# 🔍 AI PR Review Assistant

### Paste a Pull Request. Get a Structured Code Review.

---

## 📌 Overview

AI PR Review Assistant is a code review tool that takes a GitHub pull request link and generates a structured review for every changed Python file.

It combines a static analysis pass (Python `ast`) with LLM reasoning (Google Gemini) and the repository's own README/CONTRIBUTING conventions, so the feedback is grounded in facts instead of being generic.

Each review contains severity-ranked issues, line references, and concrete suggested fixes.

---

## ✨ Features

- 🔗 Fetches real PR diffs directly from the GitHub API
- 🧪 Static analysis pass (bare `except`, `eval`/`exec`, hardcoded secrets, missing docstrings)
- 📚 Repo-aware reviews using the project's README/CONTRIBUTING
- 🤖 Structured LLM output (severity, category, line, message, suggestion)
- 🚦 Three severity levels: critical, warning, nit
- 💡 Suggested fix for every issue
- 🔁 Model fallback chain to handle per-model quota and overload errors
- ⚡ On-disk result cache, so repeat reviews cost zero API calls
- 📊 Evaluation harness measuring recall and false positives
- 🖥️ Clean web dashboard

---

## 🚦 Severity Levels

| Level    | Meaning                                              |
| -------- | ---------------------------------------------------- |
| Critical | Security issue or bug that will break things         |
| Warning  | Likely bug or bad practice                           |
| Nit      | Minor style or cleanup suggestion                    |

---

## 🏗️ Architecture

```
GitHub PR URL
    │
    ▼
Fetch PR Diff (GitHub API)
    │
    ▼
Split Diff Per File
    │
    ├── Non-Python File ──▶ Skipped
    │
    └── Python File
            │
            ▼
      Rebuild "After" Code
            │
            ▼
   Static Analysis (Python ast)
            │
            ▼
   Repo Conventions (README / CONTRIBUTING)
            │
            ▼
   Gemini Review (model fallback chain)
            │
            ▼
   Structured JSON Review
            │
            ▼
   Disk Cache ──▶ Dashboard
```

---

## 🛠️ Tech Stack

| Category        | Technology                     |
| --------------- | ------------------------------ |
| Language        | Python                         |
| Backend         | FastAPI, Uvicorn               |
| LLM             | Google Gemini API              |
| Static Analysis | Python `ast` module            |
| Integration     | GitHub REST API                |
| Data Validation | Pydantic                       |
| Frontend        | HTML, CSS, JavaScript          |

---

## 📊 Evaluation

`python eval/run_eval.py` runs the full pipeline on a labelled set of code samples.

| Metric               | Result        |
| -------------------- | ------------- |
| Seeded bugs detected | **6 / 6**     |
| Recall               | **100%**      |
| Clean samples flagged | **0 / 2**    |
| False positive rate  | **0%**        |

> Note: This is a small starter set of textbook bugs (hardcoded secret, SQL injection, `eval`, bare `except`, unbound variable, mutable default argument). "Detected" means an issue of the right category was flagged, not that the exact line was verified.

---

## 📂 Project Structure

```
pr-review-assistant/
│
├── app/
│   ├── main.py             # FastAPI app and endpoints
│   ├── models.py           # Pydantic request/response schemas
│   ├── github_fetcher.py   # PR diff and repo conventions from GitHub
│   ├── diff_parser.py      # Per-file diff splitting, "after" code rebuild
│   ├── static_analysis.py  # AST-based checks
│   ├── llm_review.py       # Gemini call with model fallback
│   └── cache.py            # On-disk result cache
│
├── static/
│   └── index.html          # Web dashboard
│
├── eval/
│   ├── test_cases.py       # Labelled samples
│   └── run_eval.py         # Recall / false-positive report
│
├── test_samples/
│