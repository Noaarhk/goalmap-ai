"""
DEPRECATED: Discovery no longer uses LangGraph.
The pipeline is now implemented as plain async functions in pipeline.py.

This module is kept for backward compatibility but will be removed in a future version.
"""

import warnings

warnings.warn(
    "app.agents.discovery.graph is deprecated. "
    "Discovery now uses plain async functions in app.agents.discovery.pipeline.",
    DeprecationWarning,
    stacklevel=2,
)


def get_graph(checkpointer=None):
    """Deprecated. Discovery no longer uses a graph."""
    raise NotImplementedError(
        "Discovery graph has been removed. Use pipeline functions directly."
    )


discovery_graph = None
