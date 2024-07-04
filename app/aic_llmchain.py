from langgraph.graph.graph import CompiledGraph

from app.graph import GraphPrepare

_printed = set()


class AICLLMChain:
    def call(self, question) -> [CompiledGraph, str]:
        return GraphPrepare().compiled_graph, {"messages": ("user", question)}


aicLLMChain = AICLLMChain()
