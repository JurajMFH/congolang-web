import sys
import os

# Add the harvesters directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'harvesters'))

from harvester_lexilogos import normalize_historical_orthography

test_cases = [
    ("mwaana", "mwäna"), # Rule 1
    ("mwana", "mwan'"),   # Rule 2 (len 5 > 4)
    ("ana", "ana"),       # Rule 2 (len 3 <= 4)
    ("mwaana", "mwän'"),  # Rule 1 + Rule 2? Wait.
    ("ki", "ki"),         # Rule 2 (len 2 <= 4)
    ("kiti", "kiti"),     # Rule 2 (len 4 <= 4)
    ("kituba", "kitub'"), # Rule 2 (len 6 > 4)
    ("looba", "löba"),    # Rule 1
    ("loobaa", "löbä"),   # Rule 1? No, loobaa -> löba -> löb'. Wait.
]

print("Testing Normalization Logic:")
for original, expected in test_cases:
    # Note: my implementation applied Rule 1 then Rule 2.
    # mwaana -> (Rule 1) mwäna -> (Rule 2) mwän'
    actual = normalize_historical_orthography(original)
    print(f"Original: {original} -> Actual: {actual}")
