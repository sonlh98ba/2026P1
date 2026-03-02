import re

def normalize(msg: str) -> str:
    if not msg:
        return ""

    msg = msg.lower()

    # UUID
    msg = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '<uuid>', msg)

    # numbers
    msg = re.sub(r'\b\d+\b', '<num>', msg)

    # quoted strings
    msg = re.sub(r'\".*?\"', '<str>', msg)
    msg = re.sub(r"\'.*?\'", '<str>', msg)

    # extra spaces
    msg = re.sub(r'\s+', ' ', msg)

    return msg.strip()