from app.diff_parser import extract_new_code
from app.static_analysis import analyze_python_code

SAMPLE_DIFF = """diff --git a/demo.py b/demo.py
index 111..222 100644
--- a/demo.py
+++ b/demo.py
@@ -1,4 +1,6 @@
 import os
+API_KEY = "sk-live-abc123"
 
 def run(cmd):
-    return os.system(cmd)
+    try:
+        return eval(cmd)
+    except:
+        pass
"""

new_code = extract_new_code(SAMPLE_DIFF)
print("--- Rebuilt code ---")
print(new_code)

print("\n--- Static flags (fragment mode) ---")
for flag in analyze_python_code(new_code, is_fragment=True):
    print(" -", flag)