"""Riffin's importable package and lazy ADK root_agent export."""

# 1. Package metadata imports without starting Streamlit or contacting a provider.
DISPLAY_NAME = "Riffin’"

__all__ = ["DISPLAY_NAME", "root_agent"]


# 2. The offline catalog UI and seed script need not import ADK eagerly.
def __getattr__(name: str):
    """Expose the Lab 5 root and conventional agent module on demand."""
    if name in ("root_agent", "agent"):
        from importlib import import_module

        module = import_module(".agent", __name__)
        return module if name == "agent" else module.root_agent
    raise AttributeError(name)
