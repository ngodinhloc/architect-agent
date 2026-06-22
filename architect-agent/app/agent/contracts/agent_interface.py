from langgraph.graph import MessagesState


class ArchitectState(MessagesState):
    conversation_id: str = ""
    requirement: str = ""
    raw_history: list[dict] = []
    user_intent: str = "plan"           # "plan" | "accept" | "refine"
    prior_solution: dict | None = None  # solution from the previous conversation turn (refine context)
    solution: dict | None = None
    solution_review_comments: list[str] = []
    solution_approved: bool = False
    tickets: list[dict] = []
    ticket_review_comments: list[str] = []
    tickets_approved: bool = False
    final_reply: dict | None = None
