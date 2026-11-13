"""Model usage accounting; all log fields are numeric or fixed agent names."""

# 1. Published paid-tier Gemini 3.6 Flash rates, dated by Google pricing.
from datetime import date
import logging

RATES_2026 = {"input": 0.75, "output": 3.75, "cached": 0.075}
RATES_2027 = {"input": 1.50, "output": 7.50, "cached": 0.15}
LOGGER = logging.getLogger("riffin.usage")


def usage_from_response(response, agent: str) -> dict | None:
    """Read native ADK usage; return None when provider supplied no counts."""
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return None
    model = getattr(response, "model_version", None) or "unknown"
    prompt = max(0, getattr(usage, "prompt_token_count", 0) or 0)
    cached = min(prompt, max(0, getattr(usage, "cached_content_token_count", 0) or 0))
    output = max(0, getattr(usage, "candidates_token_count", 0) or 0)
    thoughts = max(0, getattr(usage, "thoughts_token_count", 0) or 0)
    rates = (RATES_2026 if date.today() < date(2027, 1, 1) else RATES_2027) if model.startswith("gemini-3.6-flash") else None
    estimate = round(((prompt - cached) * rates["input"] + cached * rates["cached"]
                      + (output + thoughts) * rates["output"]) / 1_000_000, 8) if rates else None
    entry = {"agent": agent, "model": model, "input_tokens": prompt,
             "cached_tokens": cached, "output_tokens": output,
             "thinking_tokens": thoughts, "estimated_usd": estimate}
    LOGGER.info("model_usage agent=%s model=%s input=%d cached=%d output=%d thinking=%d estimated_usd=%s",
                agent, model, prompt, cached, output, thoughts, estimate)
    return entry


def summarize_usage(entries: list[dict]) -> dict:
    """Summarize one turn without persisting user prompts or identity."""
    return {"model_calls": len(entries),
            "input_tokens": sum(row["input_tokens"] for row in entries),
            "output_tokens": sum(row["output_tokens"] + row["thinking_tokens"] for row in entries),
            "estimated_usd": round(sum(row["estimated_usd"] or 0 for row in entries), 8)
            if entries and all(row["estimated_usd"] is not None for row in entries) else None}
