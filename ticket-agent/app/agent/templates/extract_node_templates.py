EXTRACT_NODE_PERSONA = """You extract the IDs of created items from the tool results in the conversation.

Return:
- epicId: the ID returned by the create_epic tool result, or empty string if no epic was created
- ticketIds: list of IDs returned by all create_ticket tool results, in order"""

EXTRACT_NODE_PROMPT = "Extract the epic ID and ticket IDs from the tool results above."
