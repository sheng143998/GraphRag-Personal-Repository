from __future__ import annotations

from collections.abc import Callable
from typing import Any


SUPPORT_SUPERVISOR_TAG = "support-supervisor"


def support_node_runnable(node_name: str, func: Callable[..., Any]) -> Any:
    """Wrap a support supervisor node as a LangChain Runnable."""
    from langchain_core.runnables import RunnableLambda

    return RunnableLambda(func).with_config(
        {
            "run_name": node_name,
            "tags": [SUPPORT_SUPERVISOR_TAG, node_name],
        }
    )
