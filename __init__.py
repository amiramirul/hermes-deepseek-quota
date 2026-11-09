"""deepseek-quota — agent-side half of the DeepSeek quota chip.

This package contributes **no** tools, hooks or platforms. It exists so the
dashboard plugin API (``dashboard/plugin_api.py``) is importable while the
plugin is listed in ``plugins.enabled``; the desktop chip that consumes it
lives in ``$HERMES_HOME/desktop-plugins/deepseek-quota/plugin.js``.
"""

from __future__ import annotations


def register(ctx) -> None:  # noqa: ARG001 - nothing to register, intentionally empty
    """No agent-side registrations; the value is the dashboard API route."""
    return None
