import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from filter_code_nonsense_pass2 import is_code_noise_pass2

test_cases = [
    ("Mwana kele na ndako.", False), # Valid Kituba
    ("Beto kele na `kode` awa", "backtick_match"),
    ("Luka na [Google](https://google.com)", "md_link_match"),
    ("Beto kele **makasi**", "md_bold_match"),
    ("Mbote na beno @juraj", "mention_match"),
    ("Kisalu ya api_key me lungisa", "snake_case_match"),
    ("Nsangu na /usr/local/bin/python", "path_match"),
    ("Beto kele na plugin sika", "keyword_match"),
    ("ROC_BRAZZAVILLE", False), # Wait, SNAKE_CASE_REGEX in my script handles [a-zA-Z]+_[a-zA-Z]+
    # The script scans normalized_text. If normalized_text contains ROC_BRAZZAVILLE, it should be flagged?
    # Actually, the user said "Any word containing an underscore (like my_variable or user_extension) is 100% programming noise"
    # But they also said: "Do NOT scan or filter based on metadata columns like status, register_type... as these legitimately contain essential system tags with underscores (e.g., ROC_BRAZZAVILLE)"
    # This implies that if "ROC_BRAZZAVILLE" appears INSIDE the text (normalized_text), it MIGHT be noise or it might be legitimate.
    # However, usually ROC_BRAZZAVILLE is a metadata tag.
    # Let's see if ROC_BRAZZAVILLE is in the text.
]

print("Verifying Pass 2 Regex Heuristics:")
passed = 0
for text, expected in test_cases:
    actual = is_code_noise_pass2(text)
    if (not actual and not expected) or (actual == expected):
        print(f"[PASS] '{text[:30]}...' -> {actual}")
        passed += 1
    else:
        print(f"[FAIL] '{text[:30]}...' -> Expected: {expected}, Actual: {actual}")

print(f"\nVerification: {passed}/{len(test_cases)} passed.")
if passed == len(test_cases):
    sys.exit(0)
else:
    sys.exit(1)
