"""Optional application entrypoints."""

from typing import Any

__all__ = ["build_demo_config"]


def __getattr__(name: str) -> Any:
    if name == "build_demo_config":
        from alphalab_agent.app.streamlit_app import build_demo_config

        return build_demo_config
    raise AttributeError(name)
