"""
FastAPI app: the entry point.
Run locally with: uvicorn app.main:app --reload
"""
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.models import ReviewRequest, ReviewResponse
from app.static_analysis import analyze_python_code
from app.llm_review import get_llm_review
from app.models import ReviewRequest, ReviewResponse, PRReviewRequest, PRReviewResponse
from app.github_fetcher import fetch_pr_diff, fetch_repo_conventions
from app.diff_parser import split_diff_by_file, is_python_file, extract_new_code
from app.cache import load_cached, save_cached


app = FastAPI(
    title="AI PR Review Assistant",
    description="Submit a code diff, get back a structured, senior-engineer-style review.",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_dashboard():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/review", response_model=ReviewResponse)
def review_code(request: ReviewRequest):
    if not request.diff.strip():
        raise HTTPException(status_code=400, detail="diff cannot be empty")

    static_flags = analyze_python_code(request.diff)

    try:
        review = get_llm_review(
            filename=request.filename,
            diff=request.diff,
            static_flags=static_flags,
            repo_context=request.repo_context,
        )
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"LLM review failed: {e}")

    return review

@app.post("/review-pr", response_model=PRReviewResponse)
def review_pr(request: PRReviewRequest):
    cached = load_cached(request.pr_url)
    if cached:
        return PRReviewResponse(**cached)
    try:
        full_diff = fetch_pr_diff(request.pr_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    repo_context = fetch_repo_conventions(request.pr_url)

    file_diffs = split_diff_by_file(full_diff)

    if not file_diffs:
        raise HTTPException(status_code=400, detail="No file changes found in this PR diff.")

    reviews = []
    files_reviewed = []
    files_skipped = []

    for file_diff in file_diffs:
        if not is_python_file(file_diff.filename):
            files_skipped.append(file_diff.filename)
            continue

        new_code = extract_new_code(file_diff.diff_text)
        static_flags = analyze_python_code(new_code, is_fragment=True)

        try:
            review = get_llm_review(
                filename=file_diff.filename,
                diff=file_diff.diff_text,
                static_flags=static_flags,
                repo_context=repo_context,
            )
            reviews.append(review)
            files_reviewed.append(file_diff.filename)
        except ValueError as e:
            # Skip files that fail review rather than failing the whole PR
            files_skipped.append(f"{file_diff.filename} (error: {e})")

        result = PRReviewResponse(
        pr_url=request.pr_url,
        files_reviewed=files_reviewed,
        files_skipped=files_skipped,
        reviews=reviews,
    )

    # Only cache clean successes, never partial or failed runs
    has_errors = any("(error:" in s for s in files_skipped)
    if reviews and not has_errors:
        save_cached(request.pr_url, result.model_dump(mode="json"))

    return result