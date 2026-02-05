"""
DEPRECATED: Roadmap no longer uses LangGraph.
The pipeline is now implemented as plain async functions in pipeline.py.

This module is kept for backward compatibility but will be removed in a future version.
"""

import warnings

warnings.warn(
    "app.agents.roadmap.graph is deprecated. "
    "Roadmap now uses plain async functions in app.agents.roadmap.pipeline.",
    DeprecationWarning,
    stacklevel=2,
)


def get_graph(checkpointer=None):
    """Deprecated. Roadmap no longer uses a graph."""
    raise NotImplementedError(
        "Roadmap graph has been removed. Use pipeline functions directly."
    )


roadmap_graph = None
