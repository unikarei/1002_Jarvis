"""Conservative secret redaction for logs, errors, and publications."""
import re

_PATTERNS = (re.compile(r"(?i)Bearer\s+[^\s,;]+"), re.compile(r"(?i)(MITIR_INTEGRATION_TOKEN\s*=\s*)[^\s,;]+"), re.compile(r"-----BEGIN [^-]+PRIVATE KEY-----.*?-----END [^-]+PRIVATE KEY-----", re.DOTALL))

def redact(text: str) -> str:
    text = _PATTERNS[0].sub("Bearer [REDACTED]", text)
    text = _PATTERNS[1].sub(r"\1[REDACTED]", text)
    return _PATTERNS[2].sub("[REDACTED PRIVATE KEY]", text)
