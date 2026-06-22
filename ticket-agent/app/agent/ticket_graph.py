from langchain_anthropic import ChatAnthropic
from langchain_core.tools import StructuredTool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from app.agent.nodes.create_node import CreateNode
from app.agent.nodes.extract_node import ExtractNode
from app.agent.contracts.agent_interface import TicketState


# ┌──────────────────────────────────────────────────────────────────┐
# │                         TicketGraph                              │
# │                                                                  │
# │  START                                                           │
# │    │                                                             │
# │    ▼                                                             │
# │  create_node ◄─────────────────────────────┐                    │
# │    │                                        │                    │
# │    ├──[has tool calls]──► tools_node ───────┘                   │
# │    │                                                             │
# │    └──[no tool calls]──► extract_node                           │
# │                               │                                  │
# │                               ▼                                  │
# │                              END                                 │
# └──────────────────────────────────────────────────────────────────┘


class TicketGraph:
    def __init__(self, llm: ChatAnthropic, tools: list[StructuredTool]):
        self._llm = llm.bind_tools(tools)
        self._llm_clean = llm
        self._tools = tools

    def build(self):
        graph = StateGraph(TicketState)

        graph.add_node("create_node", CreateNode(self._llm))
        graph.add_node("tools", ToolNode(self._tools))
        graph.add_node("extract_node", ExtractNode(self._llm_clean))

        graph.add_edge(START, "create_node")
        graph.add_conditional_edges("create_node", tools_condition, {"tools": "tools", END: "extract_node"})
        graph.add_edge("tools", "create_node")
        graph.add_edge("extract_node", END)

        return graph.compile()
