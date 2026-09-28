"""
Curated evaluation dataset: code samples with KNOWN issues (labeled by us).
Each case has expected_categories — the categories of bugs we know exist.
'clean' cases have no real issues, used to measure false positive rate.
"""

TEST_CASES = [
    {
        "id": "hardcoded_secret",
        "filename": "config.py",
        "code": '''API_KEY = "sk-live-abc123xyz789"

def connect():
    return API_KEY
''',
        "expected_categories": ["security"],
        "is_clean": False,
    },
    {
        "id": "sql_injection",
        "filename": "db.py",
        "code": '''def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    return execute(query)
''',
        "expected_categories": ["security"],
        "is_clean": False,
    },
    {
        "id": "eval_usage",
        "filename": "calc.py",
        "code": '''def calculate(expression):
    return eval(expression)
''',
        "expected_categories": ["security"],
        "is_clean": False,
    },
    {
        "id": "bare_except",
        "filename": "handler.py",
        "code": '''def process(data):
    try:
        return data["value"] / data["divisor"]
    except:
        pass
''',
        "expected_categories": ["bug"],
        "is_clean": False,
    },
    {
        "id": "unbound_variable",
        "filename": "risky.py",
        "code": '''def parse(text):
    try:
        result = int(text)
    except ValueError:
        pass
    return result
''',
        "expected_categories": ["bug"],
        "is_clean": False,
    },
    {
        "id": "mutable_default_arg",
        "filename": "utils.py",
        "code": '''def add_item(item, items=[]):
    items.append(item)
    return items
''',
        "expected_categories": ["bug"],
        "is_clean": False,
    },
    {
        "id": "clean_simple_function",
        "filename": "math_utils.py",
        "code": '''def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b
''',
        "expected_categories": [],
        "is_clean": True,
    },
    {
        "id": "clean_with_proper_error_handling",
        "filename": "safe_parser.py",
        "code": '''def parse_int(text: str) -> int | None:
    """Parse a string to int, returning None if invalid."""
    try:
        return int(text)
    except ValueError:
        return None
''',
        "expected_categories": [],
        "is_clean": True,
    },
]