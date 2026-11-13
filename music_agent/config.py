"""Resolve provider configuration on the server without exposing credentials."""

# 1. Standard-library configuration keeps package imports free of UI side effects.
from collections.abc import Mapping
from dataclasses import dataclass, field
import os


# 2. Suppress the credential in repr, including accidental debug output.
@dataclass(frozen=True)
class GoogleKeyConfig:
    """Server-only credential and a safe, non-secret configuration status."""

    api_key: str | None = field(default=None, repr=False)
    source: str = "missing"

    @property
    def configured(self) -> bool:
        """Report presence only; this does not validate the key with Google."""
        return self.api_key is not None


# 3. Prefer a nonblank Streamlit Secret, then the server process environment.
def resolve_google_api_key(
    secrets: Mapping[str, object] | None = None,
    environ: Mapping[str, str] | None = None,
) -> GoogleKeyConfig:
    """Resolve GOOGLE_API_KEY without making a provider call or logging its value.

    Args:
        secrets: Server-side Streamlit Secrets, or a mapping for local checks.
        environ: Process environment by default; injectable for isolated checks.

    Returns:
        A server-only credential with its source, or an explicit missing status.
        Missing, unreadable, or malformed Streamlit Secrets allow environment
        fallback. Exception details are intentionally never displayed or logged.
    """
    if secrets is not None:
        try:
            secret_value = secrets.get("GOOGLE_API_KEY")
        except (FileNotFoundError, KeyError, ValueError, OSError):
            secret_value = None
        if isinstance(secret_value, str) and secret_value.strip():
            return GoogleKeyConfig(secret_value.strip(), "Streamlit Secrets")

    environment = os.environ if environ is None else environ
    environment_value = environment.get("GOOGLE_API_KEY", "").strip()
    if environment_value:
        return GoogleKeyConfig(environment_value, "environment")
    return GoogleKeyConfig()
