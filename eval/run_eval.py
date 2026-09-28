"""
Evaluation harness: runs the full pipeline against curated test cases
and measures recall (did we catch known bugs?) and false positive rate
(did we flag issues in clean code?).

Usage: python eval/run_eval.py
"""

import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from app.static_analysis import analyze_python_code
from app.llm_review import get_llm_review
from eval.test_cases import TEST_CASES


def run_case(case):
    """Runs one test case through the pipeline, returns the result + verdict."""
    static_flags = analyze_python_code(case["code"])

    try:
        review = get_llm_review(
            filename=case["filename"],
            diff=case["code"],
            static_flags=static_flags,
        )
    except Exception as e:
        return {"id": case["id"], "error": str(e)}

    found_categories = {issue.category for issue in review.issues}
    expected_categories = set(case["expected_categories"])

    if case["is_clean"]:
        # For clean code: success = no issues flagged (or only 'nit'/'style')
        substantive_issues = [i for i in review.issues if i.category not in ("style",)]
        false_positive = len(substantive_issues) > 0
        return {
            "id": case["id"],
            "is_clean": True,
            "false_positive": false_positive,
            "num_issues_found": len(review.issues),
        }
    else:
        # For buggy code: success = at least one expected category was found
        caught = bool(found_categories & expected_categories)
        return {
            "id": case["id"],
            "is_clean": False,
            "caught": caught,
            "expected": list(expected_categories),
            "found": list(found_categories),
        }


def main():
    results = []
    for case in TEST_CASES:
        results.append(run_case(case))
        time.sleep(15)

    buggy_results = [r for r in results if not r.get("is_clean") and "error" not in r]
    clean_results = [r for r in results if r.get("is_clean") and "error" not in r]
    errors = [r for r in results if "error" in r]

    total_buggy = len(buggy_results)
    caught = sum(1 for r in buggy_results if r["caught"])
    recall = caught / total_buggy if total_buggy else 0

    total_clean = len(clean_results)
    false_positives = sum(1 for r in clean_results if r["false_positive"])
    fp_rate = false_positives / total_clean if total_clean else 0

    print("=" * 60)
    print("EVALUATION REPORT")
    print("=" * 60)

    print(f"\nBuggy code cases: {total_buggy}")
    for r in buggy_results:
        status = "✅ CAUGHT" if r["caught"] else "❌ MISSED"
        print(f"  {status} — {r['id']} (expected: {r['expected']}, found: {r['found']})")

    print(f"\nClean code cases: {total_clean}")
    for r in clean_results:
        status = "❌ FALSE POSITIVE" if r["false_positive"] else "✅ CORRECTLY CLEAN"
        print(f"  {status} — {r['id']} ({r['num_issues_found']} issues flagged)")

    if errors:
        print(f"\nErrors: {len(errors)}")
        for r in errors:
            print(f"  ⚠️  {r['id']}: {r['error']}")

    print("\n" + "=" * 60)
    print(f"RECALL: {recall:.0%} ({caught}/{total_buggy} known bugs detected)")
    print(f"FALSE POSITIVE RATE: {fp_rate:.0%} ({false_positives}/{total_clean} clean samples flagged)")
    print("=" * 60)


if __name__ == "__main__":
    main()