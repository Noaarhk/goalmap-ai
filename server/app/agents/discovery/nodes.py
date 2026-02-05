"""
DEPRECATED: Use pipeline.py instead.
This module is kept for backward compatibility.
"""

import warnings

from app.agents.discovery.pipeline import (
    analyze_turn,
    generate_chat_stream,
    llm,
)

warnings.warn(
    "app.agents.discovery.nodes is deprecated. Use app.agents.discovery.pipeline instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export for backward compatibility
__all__ = ["analyze_turn", "generate_chat_stream", "llm"]

# Legacy alias
generate_chat = generate_chat_stream
