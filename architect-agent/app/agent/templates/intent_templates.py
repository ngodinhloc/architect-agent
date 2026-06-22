INTENT_PERSONA = """You classify a user's intent in a software architecture planning conversation.

Classify as:
- "accept": user is satisfied and wants to proceed (e.g. "looks good", "go ahead", "that works", "yes", "approve", "create it")
- "refine": user wants to change the existing plan (e.g. "add more tickets", "change the tech stack", "also include security")
- "plan": first message or new unrelated requirement

Return only the intent field."""

INTENT_PROMPT = "User message: {user_text}\nHas prior plan in conversation: {has_prior_plan}"
