from typing import Literal

from langchain.globals import set_debug
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import tools_condition

from app import my_db, chain_config
from app.assistants import Assistant, PreparePrimaryAssistant, PrepareCardAssistant, CompleteOrEscalate, \
    ToCardManagementAssistant
from app.chain_config import ChainConfigEnsure
from app.global_state import State
from app.tools_card import tools_for_card_management_safe, tools_for_card_management_all
from app.utility import create_tool_node_with_fallback, create_entry_node
from IPython.display import Image, display

set_debug(False)


class GraphPrepare:
    # noinspection PyTypeChecker
    def __init__(self):
        builder = StateGraph(State)

        builder.add_node("fetch_user_info", user_info)

        # for layer#2 assistants route back to layer#1 primary assistant
        builder.add_node("leave_skill", GraphPrepare.pop_dialog_state)
        builder.add_node(
            "enter_card_management_assistant",
            create_entry_node("Card Management Assistant",
                              "card_management_assistant",
                              "block card, unblock card, cancel card or get card status",
                              "unblock card, block card, cancel card, card status")
        )

        builder.add_node("card_management_assistant", Assistant(PrepareCardAssistant()))
        builder.add_node(
            "card_management_tools",
            create_tool_node_with_fallback(tools_for_card_management_all()),
        )

        # primary assistant setup layer#1(primary assistant and tools) and layer#2(secondary assistants)
        builder.add_node("primary_assistant", Assistant(PreparePrimaryAssistant()))
        # builder.add_node("primary_assistant_tools",
        #                  create_tool_node_with_fallback(PreparePrimaryAssistant.tools_primary()))

        builder.add_conditional_edges("fetch_user_info", GraphPrepare.route_to_workflow)
        builder.add_edge("enter_card_management_assistant", "card_management_assistant")
        builder.add_edge("card_management_tools", "card_management_assistant")
        builder.add_conditional_edges("card_management_assistant", GraphPrepare.route_card_management)
        builder.add_edge("leave_skill", "primary_assistant")
        builder.add_conditional_edges(
            "primary_assistant",
            GraphPrepare.route_primary_assistant,
            {
                "enter_card_management_assistant": "enter_card_management_assistant",
                # "primary_assistant_tools": "primary_assistant_tools",
                END: END,
            },
        )
        # builder.add_edge("primary_assistant_tools", "primary_assistant")
        builder.add_edge("primary_assistant", END)

        builder.set_entry_point("fetch_user_info")
        # Compile graph TODO change to AsyncSqliteSaver for astream
        # memory = AsyncSqliteSaver.from_conn_string(":memory:")
        memory = SqliteSaver.from_conn_string(":memory:")
        self.compiled_graph: CompiledGraph = builder.compile(
            checkpointer=memory,
            # Let the user approve or deny the use of sensitive tools
            interrupt_before=[
                # "fetch_user_info",
            ],
        )

        # Assuming `self.compiled_graph.get_graph(xray=True).draw_mermaid_png()` returns an image object
        image = self.compiled_graph.get_graph(xray=True).draw_mermaid_png()

        # Display the image
        display(Image(image))

        # Save the image to a path
        with open('/Users/choikokhou/Documents/workspace/sl/engine/model_rnd/app/graph.png', 'wb') as f:
            f.write(image)

    # This node will be shared for exiting all specialized assistants
    @staticmethod
    def pop_dialog_state(state: State) -> dict:
        """Pop the dialog stack and return to the main assistant.

        This lets the full graph explicitly track the dialog flow and delegate control
        to specific sub-graphs.
        """
        messages = []
        if state["messages"][-1].tool_calls:
            # Note: Doesn't currently handle the edge case where the llm performs parallel tool calls
            messages.append(
                ToolMessage(
                    content="Resuming dialog with the host assistant. Please reflect on the past conversation and "
                            "assist the user as needed.",
                    tool_call_id=state["messages"][-1].tool_calls[0]["id"],
                )
            )
        return {
            "dialog_state": "pop",
            "messages": messages,
        }

    @staticmethod
    def route_card_management(
        state: State,
    ) -> Literal[
        "leave_skill", "card_management_tools", "__end__"
    ]:
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
        if did_cancel:
            return "leave_skill"
        tool_names = [t.name for t in tools_for_card_management_safe()]
        if all(tc["name"] in tool_names for tc in tool_calls):
            return "card_management_tools"  # when is safe tools you can do different agent

        return "card_management_tools"

    @staticmethod
    def route_primary_assistant(
        state: State,
    ) -> Literal[
        "primary_assistant_tools",
        "enter_card_management_assistant",
        "__end__",
    ]:
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        if tool_calls:
            if tool_calls[0]["name"] == ToCardManagementAssistant.__name__:
                return "enter_card_management_assistant"
            return END
            # return "primary_assistant_tools"
        raise ValueError("Invalid route")

    @staticmethod
    def route_to_workflow(
        state: State,
    ) -> Literal[
        "primary_assistant",
        "card_management_assistant",
    ]:
        """If we are in a delegated state, route directly to the appropriate assistant."""

        print("--- route_to_workflow ---")

        dialog_state = state.get("dialog_state")
        if not dialog_state:
            return "primary_assistant"
        return dialog_state[-1]


def user_info(state: State):
    """get user info"""

    print("--- (user_info) Fetching user information... ---")
    print(state)

    config = ChainConfigEnsure()  # Fetch from the context
    access_token = config[chain_config.ACCESS_TOKEN]
    if not access_token:
        raise ValueError("Token not valid")

    user_id = access_token
    user = my_db.get_user_by_id(user_id)
    if user:
        return {"user_valid": True}  # "user_inf o": user, "access_token": str(user_id)
    else:
        return {}
