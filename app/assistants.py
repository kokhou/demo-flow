import os
from datetime import datetime
from typing import Dict

from dotenv import load_dotenv
from langchain_core.globals import set_debug
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI

from app.base_prepare_assistant import BasePrepareAssistant
from app.global_state import State
from app.tools_card import tools_for_card_management_all

set_debug(False)
load_dotenv()

# os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

# Recommended
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "MyTHEO account opening test"

llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)


# handling query
class Assistant:

    def __init__(self, base_prepare_assistant: BasePrepareAssistant):
        self.base_prepare_assistant = base_prepare_assistant

    def __call__(self, state: State, config: RunnableConfig) -> Dict:

        self.base_prepare_assistant.state = state
        self.runnable = self.base_prepare_assistant.get_assistant_runnable()

        while True:
            result = self.runnable.invoke(state, config)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


# complete or escalate route by LLM from assistant to assistant
class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control of the dialog to the main assistant,
    who can re-route the dialog based on the user's needs."""

    cancel: bool = True
    reason: str

    class Config:
        schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User changed their mind about the current task.",
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            },
            "example 3": {
                "cancel": False,
                "reason": "I need to search the user's emails or calendar for more information.",
            },
        }


class ToCardManagementAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle card management. (e.g. unblocking, blocking, canceling a card or get status.)"""
    request: str = Field(
        description="Any additional information or requests from the user regarding the Card Management Assistant."
    )

    class Config:
        schema_extra = {
            "example": {
                "request": "Can you help me unblock my card and cancel card?",
            }
        }


class PreparePrimaryAssistant(BasePrepareAssistant):

    # layer 1 tools
    @staticmethod
    def tools_primary():
        return []

    # layer 2 tools
    @staticmethod
    def tools_secondary():
        return [ToCardManagementAssistant]  # add more assistant here

    def init_assistant_runnable(self) -> Runnable:
        primary_assistant_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful customer support assistant for Card Management. Your primary role is to help "
                    "user manage their card. If a customer requests to manage card delegate the task to the "
                    "appropriate specialized assistant by invoking the corresponding tool. You are not able to make "
                    "these types of changes yourself. Only the specialized assistants are given permission to do this "
                    "for the user. The user is not aware of the different specialized assistants, so do not mention "
                    "them; just quietly delegate through function calls. Provide detailed information to the "
                    "customer, and always double-check the database before concluding that information is unavailable."
                ),
                ("placeholder", "{messages}"),
            ]
        ).partial(time=datetime.now())

        return primary_assistant_prompt | llm.bind_tools(
            PreparePrimaryAssistant.tools_primary() + PreparePrimaryAssistant.tools_secondary())


class PrepareCardAssistant(BasePrepareAssistant):

    def init_assistant_runnable(self) -> Runnable:
        _card_assistant = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a specialized assistant for handling Card service. "
                    "The primary assistant delegates work to you whenever the user needs help for Card Management "
                    "including unblock card, block card, cancel card and card status inquiry. If you need more "
                    "information or the customer changes their mind, escalate the task back to the main assistant. "
                    "Remember that a suggestion portfolio isn't completed until after the relevant tool has "
                    "successfully been used."
                    "\nCurrent time: {time}."
                    "\n\nIf the user needs help, and none of your tools are appropriate for it, then "
                    'CompleteOrEscalate" the dialog to the host assistant. Do not waste the user\'s time. Do not make '
                    'up invalid tools or functions.'
                    "\n\nSome examples for which you should CompleteOrEscalate:\n"
                    " - The card has been unblocked.\n"
                    " - The card has been blocked.\n"
                    " - The card has been cancelled.\n"
                    " - The card status is unblocked no, block yes ...\n"
                ),
                ("placeholder", "{messages}"),
            ]
        ).partial(time=datetime.now())
        return _card_assistant | llm.bind_tools(
            tools_for_card_management_all() + [CompleteOrEscalate]
        )
