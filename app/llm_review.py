"""
LLM reasoning pass, using Google Gemini (free tier) with a model fallback chain.

Free-tier quota is tracked per model, so if one model is out of quota,
overloaded, or unavailable, we move on to the next one.
"""

import os
import json
import time
from google import genai
from google.genai import types
from typing import List, Optional

from app.models import ReviewResponse, Issue, Severity

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Tried in this order. Lighter models first (usually less busy).
MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.8-flash",
]

SYSTEM_PROMPT = """You are a senior software engineer performing a code review.
You will be given: a code diff, a list of static-analysis flags already found by a linter,
and optionally the repo's coding conventions.

Your job: identify real bugs, security issues, and style problems that MATTER.
Do not repeat every static analysis flag verbatim — use them as hints, but add your own reasoning.
Do not invent issues that aren't there. If the code looks fine, say so.

Respond with ONLY a JSON object (no markdown fences, no preamble) matching this exact schema:
{
  "summary": "1-2 sentence overall verdict",
  "issues": [
    {
      "line": <int or null>,
      "severity": "critical" | "warning" | "nit",
      "category": "bug" | "security" | "style" | "performance",
      "message": "clear explanation",
      "suggestion": "suggested fix or code snippet, or null"
    }
  ]
}
"""


def build_user_prompt(filename: str, diff: str, static_flags: List[str], repo_context: Optional[str]) -> str:
    parts = [f"Filename: {filename}", "", "Code diff:", "```", diff, "```"]

    if static_flags:
        parts.append("\nStatic analysis flags found:")
        parts.extend(f"- {f}" for f in static_flags)
    else:
        parts.append("\nStatic analysis flags found: none")

    if repo_context:
        parts.append(f"\nRepo coding conventions:\n{repo_context}")

    return "\n".join(parts)


def _call_with_fallback(user_prompt: str):
    """Tries each model in MODELS. Returns the response, or raises ValueError."""
    errors = []
    response = None

    for pass_num in range(2):
        saw_transient = False

        for model_name in MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        max_output_tokens=1500,
                    ),
                )
                print(f"Reviewed with {model_name}")
                return response
            except Exception as e:
                msg = str(e)
                errors.append(msg)
                print(f"{model_name} failed: {msg[:110]}")
                if "503" in msg or "UNAVAILABLE" in msg or ("429" in msg and "PerDay" not in msg):
                    saw_transient = True

        if pass_num == 0 and saw_transient:
            print("All models failed once. Waiting 20s before a second pass...")
            time.sleep(20)
        else:
            break

    permanent = all(
        ("PerDay" in m) or ("404" in m) or ("NOT_FOUND" in m) for m in errors
    )
    if permanent:
        raise ValueError(
            "Daily free-tier limit reached on all available models. Please try again tomorrow."
        )
    raise ValueError("The AI service is busy right now. Please try again in a minute or two.")


def get_llm_review(filename: str, diff: str, static_flags: List[str], repo_context: Optional[str] = None) -> ReviewResponse:
    user_prompt = build_user_prompt(filename, diff, static_flags, repo_context)

    response = _call_with_fallback(user_prompt)

    raw_text = response.text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}\nRaw output: {raw_text}")

    issues = [
        Issue(
            line=issue.get("line"),
            severity=Severity(issue["severity"]),
            category=issue["category"],
            message=issue["message"],
            suggestion=issue.get("suggestion"),
        )
        for issue in parsed.get("issues", [])
    ]

    return ReviewResponse(
        filename=filename,
        summary=parsed.get("summary", ""),
        issues=issues,
        static_analysis_flags=static_flags,
    )