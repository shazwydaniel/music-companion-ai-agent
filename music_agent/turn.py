"""Invocation-local evidence, separate from shared public catalog/index data."""

# 1. Context variables isolate simultaneous visitors and nested AgentTool calls.
from contextvars import ContextVar
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Callable


@dataclass
class TurnEvidence:
    """Keep source evidence privately; expose only the bounded trace columns."""

    prompt: str = field(repr=False)
    allow_web: bool = False
    search_query: str = field(default="", repr=False)
    retriever: Any = field(default=None, repr=False)
    trace: list[dict] = field(default_factory=list)
    results: list[dict] = field(default_factory=list, repr=False)
    web_sources: list[dict] = field(default_factory=list)
    usage: list[dict] = field(default_factory=list)
    started: dict = field(default_factory=dict, repr=False)
    cache: dict = field(default_factory=dict, repr=False)
    failure_code: str | None = None
    on_activity: Callable[[dict], None] | None = field(default=None, repr=False)

    def announce(self, agent: str, tool: str, status: str) -> None:
        """Push controlled runtime activity, without arguments or model thoughts."""
        if self.on_activity:
            self.on_activity({"agent": agent, "tool": tool, "status": status})

    def record(self, agent: str, tool: str, outcome: str, started: float) -> None:
        """Record names, a controlled status, and duration, never arguments."""
        if len(self.trace) < 40:
            self.trace.append({
                "agent": agent, "tool": tool, "outcome": outcome,
                "elapsed_ms": round((perf_counter() - started) * 1000, 1),
            })
        self.announce(agent, tool, outcome)


CURRENT_TURN: ContextVar[TurnEvidence | None] = ContextVar("riffin_turn", default=None)
