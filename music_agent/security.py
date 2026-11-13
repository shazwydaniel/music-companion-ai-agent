"""Deterministic input and SQLite query boundaries for the public demo."""

# 1. Mask common personal identifiers before a prompt reaches a provider.
import re

import sqlglot
from sqlglot import exp

_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
_SECRET = re.compile(r"\b(?:AIza[\w-]{20,}|sk-[\w-]{20,})\b")


def mask_pii(text: str) -> str:
    """Replace likely credentials, email addresses, card numbers and phone numbers.

    This is a conservative local mask, not a complete PII detector. Preserve
    music quantities such as BPM, bar counts and chord names.
    """
    text = _SECRET.sub("[REDACTED_KEY]", text)
    text = _EMAIL.sub("[REDACTED_EMAIL]", text)
    text = _CARD.sub("[REDACTED_NUMBER]", text)
    return _PHONE.sub("[REDACTED_PHONE]", text)


# 2. Block attempts to override instructions or extract private runtime data.
_INJECTION = re.compile(
    r"\b(?:ignore|disregard|override|forget)\b.{0,70}\b(?:previous|prior|system|developer|instructions?|rules?)\b|"
    r"\b(?:reveal|print|show|dump|exfiltrate|send)\b.{0,70}\b(?:api[ _-]?key|secrets?|system prompt|developer message|environment variables?)\b|"
    r"\b(?:you are now|act as)\b.{0,50}\b(?:system|developer|unrestricted|jailbreak)\b|"
    r"\[(?:im_start|start_header_id)\]|<\|(?:im_start|start_header_id)\|>|"
    r"\b(?:tool|function)\s*[:.]\s*(?:delete|drop|update|insert|write)\b",
    re.I | re.S,
)


def prompt_injection_request(text: str) -> bool:
    """Catch explicit instruction takeover or secret extraction at ingress."""
    return bool(_INJECTION.search(text))


# 3. Parse a single SQLite statement and reject everything except SELECT ASTs.
def is_sql_mutation(sql: str) -> bool:
    """Return True for writes, commands, malformed or multiple SQL statements.

    Args:
        sql: Candidate SQLite statement; parameters remain bound separately.

    Returns:
        True unless the parsed statement is one plain, read-only SELECT or
        UNION of SELECTs, with no write/command node anywhere in its AST.
    """
    try:
        statements = sqlglot.parse(sql, read="sqlite", error_level="RAISE")
    except (sqlglot.errors.ParseError, ValueError, TypeError):
        return True
    if len(statements) != 1 or statements[0] is None:
        return True
    root = statements[0]
    if not isinstance(root, (exp.Select, exp.Union)):
        return True
    denied = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create,
              exp.Alter, exp.Command, exp.Pragma, exp.Attach, exp.Detach)
    return any(isinstance(node, denied) for node in root.walk())
