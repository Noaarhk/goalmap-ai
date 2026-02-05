"""
DEPRECATED: Use pipeline.py instead.
This module is kept for backward compatibility.
"""

import warnings

from app.agents.roadmap.pipeline import (
    generate_actions,
    generate_skeleton,
    llm,
)

warnings.warn(
    "app.agents.roadmap.nodes is deprecated. Use app.agents.roadmap.pipeline instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export for backward compatibility
__all__ = ["generate_skeleton", "generate_actions", "llm"]
