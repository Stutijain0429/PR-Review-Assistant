"""
Quick local test — bypasses the API server, calls the pipeline directly.
Usage: python test_local.py test_samples/buggy_example.py
"""
from dotenv import load_dotenv
load_dotenv()
import sys
import json
from app.static_analysis import analyze_python_code
from app.llm_review import get_llm_review

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_local.py <path_to_python_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    with open(filepath, "r") as f:
        code = f.read()

    print("=" * 60)
    print("STEP 1: Static analysis")
    print("=" * 60)
    flags = analyze_python_code(code)
    for flag in flags:
        print(f"  - {flag}")
    if not flags:
        print("  (no flags)")

    print("\n" + "=" * 60)
    print("STEP 2: LLM review")
    print("=" * 60)
    review = get_llm_review(filename=filepath, diff=code, static_flags=flags)
    print(json.dumps(review.model_dump(), indent=2))


if __name__ == "__main__":
    main()