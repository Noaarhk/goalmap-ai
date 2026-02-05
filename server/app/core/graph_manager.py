"""
DEPRECATED: Agents now use plain async functions instead of LangGraph.

This module is no longer used and will be removed in a future version.
Both Discovery and Roadmap agents have been simplified to direct function calls.
"""

import warnings

warnings.warn(
    "app.core.graph_manager is deprecated. "
    "Agents now use plain async functions in their respective pipeline modules.",
    DeprecationWarning,
    stacklevel=2,
)


class GraphManager:
    """
    DEPRECATED: No longer used.
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "GraphManager has been removed. Use pipeline functions directly."
        )
