"""
Static analysis pass.

Runs BEFORE the LLM call. Catches cheap, deterministic issues with plain
code parsing, then feeds these findings into the LLM prompt.

is_fragment=True means the code is a piece of a file (e.g. rebuilt from a
PR diff), so we avoid checks that would give false positives on partial code.
"""

import ast
import textwrap
from typing import List


def analyze_python_code(code: str, is_fragment: bool = False) -> List[str]:
    flags: List[str] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        if is_fragment:
            # A diff hunk is often not valid standalone Python (starts mid-function,
            # odd indentation). Try dedenting once, otherwise skip quietly.
            try:
                tree = ast.parse(textwrap.dedent(code))
            except SyntaxError:
                return []
        else:
            flags.append(f"SyntaxError: code does not parse ({e.msg} at line {e.lineno})")
            return flags

    imported_names = set()
    used_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            flags.append(f"Line {node.lineno}: bare 'except:' clause — catches all exceptions, hides bugs")

        if isinstance(node, ast.FunctionDef):
            n_args = len(node.args.args)
            if n_args > 6:
                flags.append(f"Line {node.lineno}: function '{node.name}' has {n_args} arguments — consider refactoring")

            if not node.name.startswith("_"):
                if ast.get_docstring(node) is None:
                    flags.append(f"Line {node.lineno}: public function '{node.name}' has no docstring")

        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name.split(".")[0])
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)
        if isinstance(node, ast.Name):
            used_names.add(node.id)

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and any(
                    kw in target.id.lower() for kw in ["password", "secret", "api_key", "token"]
                ):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        flags.append(
                            f"Line {node.lineno}: possible hardcoded secret in variable '{target.id}'"
                        )

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec"):
                flags.append(f"Line {node.lineno}: use of '{node.func.id}()' — potential security risk")

    # Unused-import check only makes sense on a complete file
    if not is_fragment:
        unused = imported_names - used_names
        for name in unused:
            flags.append(f"Import '{name}' appears unused")

    return flags