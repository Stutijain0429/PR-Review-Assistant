"""
Pydantic schemas used across the app.
These define the shape of data going IN (a diff to review)
and coming OUT (a structured review).
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"   # bug/security issue that will break things
    WARNING = "warning"     # likely bug or bad practice
    NIT = "nit"             # style/minor suggestion


class ReviewRequest(BaseModel):
    """What the client sends us to get a review."""
    filename: str = Field(..., description="Name of the file being reviewed, e.g. 'main.py'")
    diff: str = Field(..., description="The code diff or full file content to review")
    repo_context: Optional[str] = Field(
        None, description="Optional: coding conventions / style guide snippet for this repo"
    )

class PRReviewRequest(BaseModel):
    """What the client sends to review an entire GitHub PR."""
    pr_url: str = Field(..., description="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")

class Issue(BaseModel):
    """A single issue found in the code."""
    line: Optional[int] = Field(None, description="Approximate line number, if known")
    severity: Severity
    category: str = Field(..., description="e.g. 'bug', 'security', 'style', 'performance'")
    message: str = Field(..., description="Human-readable explanation of the issue")
    suggestion: Optional[str] = Field(None, description="Suggested fix or code snippet")


class ReviewResponse(BaseModel):
    """What we send back: a structured code review."""
    filename: str
    summary: str = Field(..., description="1-2 sentence overall verdict")
    issues: List[Issue]
    static_analysis_flags: List[str] = Field(
        default_factory=list, description="Raw flags from the static analysis pass"
    )

class PRReviewResponse(BaseModel):
    """Full PR review: one ReviewResponse per changed Python file."""
    pr_url: str
    files_reviewed: List[str]
    files_skipped: List[str] = Field(default_factory=list, description="Non-Python files that were skipped")
    reviews: List[ReviewResponse]