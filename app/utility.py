from typing import Callable, Literal

from langchain_core.messages import ToolMessage, AIMessage, HumanMessage, ChatMessage, SystemMessage, FunctionMessage
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
from langgraph.prebuilt import ToolNode

from app.global_state import State


def handle_tool_error(state: State) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_entry_node(assistant_name: str, new_dialog_state: str, action: str, sequence: str) -> Callable:
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between "
                            f"the host assistant and the user. The user's intent is unsatisfied. Use the provided "
                            f"tools to assist the user. Remember, you are {assistant_name}, and the {action} action "
                            f"is not complete until after you have successfully invoked the "
                            f"appropriate tool If there is multiple parallel tools call, you have to follow this "
                            f"sequence {sequence}"
                            f". If the user changes their mind or needs help for other tasks, "
                            f"call the CompleteOrEscalate function to let the primary host assistant take control. Do "
                            f"not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }

    return entry_node


def create_tool_node_with_fallback(tools: list) -> RunnableWithFallbacks[dict[
    str, list[AIMessage | HumanMessage | ChatMessage | SystemMessage | FunctionMessage | ToolMessage] | dict[
        str, str] | str | object | list[Literal["primary_assistant", "card_management_assistant"]]], dict]:
    return ToolNode(tools).with_fallbacks([RunnableLambda(handle_tool_error)], exception_key="error")


def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print(f"Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)


def is_none_or_empty(value):
    if value is None:
        return True
    if isinstance(value, (str, list, tuple, set, dict)) and len(value) == 0:
        return True
    return False
