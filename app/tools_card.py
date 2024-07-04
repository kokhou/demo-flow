# Step #2: define tools

import os
from typing import List

from langchain_core.tools import tool, BaseTool
from langchain_openai import ChatOpenAI

from app import chain_config
from app.chain_config import ChainConfigEnsure
from app.config import settings

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
llm = ChatOpenAI(model=settings.default_model)

user_to_pets = {}


# noinspection PyTypeChecker
def tools_for_card_management_safe() -> List[BaseTool]:
    """Generate a set of safe tools for card management."""

    @tool
    def card_status():
        """
            Use this tool to check card status.
        """

        config = ChainConfigEnsure()  # Fetch from the context
        access_token = config[chain_config.ACCESS_TOKEN]
        if not access_token:
            raise ValueError("Token not valid")

        print("access_token#", access_token)
        user_to_pets[access_token] = {
            "unblock_card": "",
            "block_card": "",
            "cancel_card": "",
            "card_status": "Card is active"
        }
        return user_to_pets[access_token]

    return [card_status]


# noinspection PyTypeChecker
def tools_for_card_management_sensitive() -> List[BaseTool]:
    """Generate a set of sensitive tools for card management."""

    @tool
    def unblock_card(card_id: str) -> str:
        """
        Use this function to unblock a card.

        Args:
            card_id (Optional[str]): The card id is required to unblock the card, if card id not found please request from user.

        Returns:
            str: a message to confirm the card is unblocked.
        """

        user_to_pets[1] = {
            "unblock_card": card_id,
            "block_card": "",
            "cancel_card": ""
        }

        return "Card is unblocked."

    @tool
    def block_card(card_id: str) -> str:
        """
        Use this function to block a card.

        Args:
            card_id (Optional[str]): The card id is required to block the card, if card id not found please request from user.

        Returns:
            str: a message to confirm the card is blocked.
        """

        user_to_pets[1] = {
            "unblock_card": "",
            "block_card": card_id,
            "cancel_card": ""
        }

        return "Card is blocked."

    @tool
    def cancel_card(card_id: str) -> str:
        """
           Use this function to cancel a card.

           Args:
               card_id (Optional[str]): The card id is required to cancel the card, if card id not found please request from user.

           Returns:
               str: a message to confirm the card is cancel.
           """
        user_to_pets[1] = {
            "unblock_card": "",
            "block_card": "",
            "cancel_card": card_id
        }

        return "Card is canceled."

    return [unblock_card, block_card, cancel_card]


# noinspection PyTypeChecker
def tools_for_card_management_all() -> List[BaseTool]:
    """Compile all tools for card management."""

    return tools_for_card_management_safe() + tools_for_card_management_sensitive()


#
# def handle_run_time_request(user_id: str, query: str):
#     """Handle run time request."""
#     tools = tools_for_card_management_all()
#     llm_with_tools = llm.bind_tools(tools)
#     prompt = ChatPromptTemplate.from_messages(
#         [("system", "You are a helpful assistant.")],
#     )
#     chain = prompt | llm_with_tools
#     return llm_with_tools.invoke(query)
#
#
# # _unblock_card, _block_card, _cancel_card, _card_status = generate_tools_for_card_management("choi")
# #
# # print(user_to_pets)
# # print(_card_status.invoke({}))
# #
# ai_message = handle_run_time_request(
#     "eugene", "I wan unblock card and give me card status, my card id is 888."
# )
# print(ai_message.tool_calls)
# a = tools_for_card_management_sensitive()
# print(a)
# b = tools_for_card_management_sensitive()
# print(b)
