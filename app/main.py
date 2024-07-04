from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.globals import set_debug
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app import chain_config
from app.aic_llmchain import aicLLMChain
from app.chain_config import ChainConfig

set_debug(False)

app = FastAPI()

# Add the CORSMiddleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow only specified origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


class Question(BaseModel):
    question: str


_printed = set()


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


async def _llm_chain(question: str):
    try:
        chain, final_question = aicLLMChain.call(question=question)
    except HTTPException as e:
        yield "This is error"
        return

    # Create an instance of ChainConfig
    config = ChainConfig()
    config[chain_config.THREAD_ID] = 1
    config[chain_config.ACCESS_TOKEN] = 1

    # TODO print better
    events = chain.stream(final_question, config.get_config(), stream_mode="values")
    for event in events:
        _print_event(event, _printed)

    # TODO response in stream
    # async for event in chain.astream_events(final_question, config.get_config(), stream_mode="updates", version="v1"):
    #     kind = event["event"]
    #     if kind == "on_chat_model_stream":
    #         content = event["data"]["chunk"].content
    #         if content:
    #             # Empty content in the context of OpenAI or Anthropic usually means
    #             # that the model is asking for a tool to be invoked.
    #             # So we only print non-empty content
    #             print(content, end="|")
    #             yield content
    #     elif kind == "on_tool_start":
    #         print("--")
    #         print(
    #             f"Starting tool: {event['name']} with inputs: {event['data'].get('input')}"
    #         )
    #     elif kind == "on_tool_end":
    #         print(f"Done tool: {event['name']}")
    #         print(f"Tool output was: {event['data'].get('output')}")
    #         print("--")


@app.post("/")
async def ask(*, question: Question):
    return StreamingResponse(content=_llm_chain(question.question), media_type="text/event-stream", )
