from typing import Annotated, Literal, Optional

from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import TypedDict


def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the state."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_valid: str
    dialog_state: Annotated[
        list[
            Literal[
                "primary_assistant",
                "card_management_assistant",
            ]
        ],
        update_dialog_stack,
    ]
