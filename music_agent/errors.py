"""Provider error categories whose messages contain no raw request or key."""

# 1. Controlled UI statuses distinguish credentials, quotas, and failures.
import asyncio

import httpx

MESSAGES = {
    "out_of_scope": "I’m here for music: songs, chords, theory, practice and music calculations. Try a music question instead.",
    "credentials_unavailable": "Google credentials are unavailable or were rejected. Catalog browsing still works.",
    "quota": "Google quota is unavailable right now. Try again later; no automatic retry was made.",
    "timeout": "The Google request timed out. Try again when you are ready.",
    "error": "The provider or retrieval service could not complete this request. Please try again.",
    "calibration_error": (
        "The notes index could not pass its relevance checks. This is a retrieval failure, not a coverage gap."
    ),
    "no_sources": (
        "Google returned no usable grounding links. This response cannot be presented as a sourced web result."
    ),
}


def error_status(error: Exception) -> str:
    """Classify errors by type/status, without displaying exception text."""
    if isinstance(error, (asyncio.TimeoutError, TimeoutError, httpx.TimeoutException)):
        return "timeout"
    code = getattr(error, "code", None)
    response = getattr(error, "response", None)
    code = code or getattr(response, "status_code", None)
    if code in (401, 403):
        return "credentials_unavailable"
    if code == 429:
        return "quota"
    return "error"
