from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from app.agent.contracts.agent_interface import ArchitectState
from app.agent.nodes.intent_node import IntentNode
from app.agent.nodes.solution_node import SolutionNode
from app.agent.nodes.solution_review_node import SolutionReviewNode
from app.agent.nodes.plan_node import PlanNode
from app.agent.nodes.plan_review_node import PlanReviewNode
from app.agent.nodes.reply_node import ReplyNode
from app.events.rabbitmq_publisher import RabbitMQPublisher


# ┌──────────────────────────────────────────────────────────────────┐
# │                        ArchitectGraph                            │
# │                                                                  │
# │  START                                                           │
# │    │                                                             │
# │    ▼                                                             │
# │  intent_node                                                     │
# │    │                                                             │
# │    ├──[plan / refine]───────────────────────────────────────┐    │
# │    │                                                        ▼    │
# │    │                                           ┌─► solution_node │
# │    │                                           │            │    │
# │    │                                           │            ▼    │
# │    │                                           │ solution_review  │
# │    │                                  [rejected]│   │[approved]  │
# │    │                                           └───┘     │      │
# │    │                                                      ▼      │
# │    │                                           ┌─► plan_node     │
# │    │                                           │        │        │
# │    │                                           │        ▼        │
# │    │                                  [rejected]│ plan_review    │
# │    │                                           └───┘    │[approved]
# │    │                                                     ▼       │
# │    │                                               reply_node    │
# │    │                                                     │       │
# │    │                                                     ▼       │
# │    │                                                    END      │
# │    │                                                             │
# │    └──[accept]──► publishes to architecture-agent.accept ──► END │
# └──────────────────────────────────────────────────────────────────┘


class ArchitectGraph:
    def __init__(self, llm: ChatAnthropic, publisher: RabbitMQPublisher):
        self._llm = llm
        self._publisher = publisher

    def build(self):
        graph = StateGraph(ArchitectState)

        graph.add_node("intent_node", IntentNode(self._llm, self._publisher))
        graph.add_node("solution_node", SolutionNode(self._llm))
        graph.add_node("solution_review_node", SolutionReviewNode(self._llm))
        graph.add_node("plan_node", PlanNode(self._llm))
        graph.add_node("plan_review_node", PlanReviewNode(self._llm))
        graph.add_node("reply_node", ReplyNode())

        graph.add_edge(START, "intent_node")

        graph.add_conditional_edges(
            "intent_node",
            self._route_intent,
            {"accept": END, "plan": "solution_node", "refine": "solution_node"},
        )

        graph.add_edge("solution_node", "solution_review_node")
        graph.add_conditional_edges(
            "solution_review_node",
            self._route_solution_review,
            {"approved": "plan_node", "rejected": "solution_node"},
        )

        graph.add_edge("plan_node", "plan_review_node")
        graph.add_conditional_edges(
            "plan_review_node",
            self._route_plan_review,
            {"approved": "reply_node", "rejected": "plan_node"},
        )

        graph.add_edge("reply_node", END)

        return graph.compile()

    @staticmethod
    def _route_intent(state: ArchitectState) -> str:
        return state.get("user_intent", "plan")

    @staticmethod
    def _route_solution_review(state: ArchitectState) -> str:
        return "approved" if state.get("solution_approved") else "rejected"

    @staticmethod
    def _route_plan_review(state: ArchitectState) -> str:
        return "approved" if state.get("tickets_approved") else "rejected"

