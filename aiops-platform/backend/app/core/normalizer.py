import re

def normalize(msg: str) -> str:
    if not msg:
        return ""

    msg = msg.lower()

    # Normalize verbose SQLAlchemy/psycopg2 payload blocks to avoid fingerprint explosion.
    msg = re.sub(r"\[parameters:\s*\{.*?\}\]", "[parameters]", msg, flags=re.DOTALL)
    msg = re.sub(r"\[sql:\s*.*?\]", "[sql]", msg, flags=re.DOTALL)

    # UUID
    msg = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '<uuid>', msg)
    msg = re.sub(r"uuid\('[^']*'\)", "uuid(<uuid>)", msg)
    msg = re.sub(r"'[a-f0-9-]{4,}\.\.\.", "'<id>...", msg)

    # numbers
    msg = re.sub(r'\b\d+\b', '<num>', msg)

    # quoted strings
    msg = re.sub(r'\".*?\"', '<str>', msg)
    msg = re.sub(r"\'.*?\'", '<str>', msg)

    # extra spaces
    msg = re.sub(r'\s+', ' ', msg)

    return msg.strip()
