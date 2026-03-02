from app.core.normalizer import normalize

tests = [
    'relation "ledger_12345" does not exist',
    'relation "ledger_98765" does not exist',
    'division by 0',
    'division by zero',
    'user 381e587e-4 not found'
]

for t in tests:
    print(t, "=>", normalize(t))