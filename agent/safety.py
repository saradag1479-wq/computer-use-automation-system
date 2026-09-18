from urllib.parse import urlparse

ALLOWED_ACTIONS = {
    "goto", "fill", "click", "extract_text", "assert_text"
}

class SafetyError(RuntimeError):
    pass

def validate_url(url, allowed_domains):
    host = urlparse(url).hostname
    if host not in allowed_domains:
        raise SafetyError(f"Application is not allowlisted: {host}")

def validate_action(action):
    if action not in ALLOWED_ACTIONS:
        raise SafetyError(f"Action is not allowlisted: {action}")

def redact(value):
    markers = ("password", "secret", "token", "authorization", "ssn")
    if any(x in value.lower() for x in markers):
        return "[REDACTED]"
    return value
