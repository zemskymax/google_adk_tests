from a2a.types import AgentCard, AgentCapabilities, AgentSkill

SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

def get_agent_card(public_url: str) -> AgentCard:
    """Generates the agent card for the personal helper agent."""
    capabilities = AgentCapabilities(streaming=False, tools=True, push_notifications=False)

    food_ordering_skill = AgentSkill(
        id="food-ordering",
        name="Order Food",
        description="Handles the complete food ordering process by discovering and connecting to the relevant restaurant.",
        tags=["food", "ordering", "delegation"],
        examples=["I want to order a pizza", "I would like to order some pasta", "Let's get some food!", "I'll have food please"],
    )

    agent_card = AgentCard(
        name="Alex Helper Bot",
        description="A friendly personal food ordering AI assistant that helps you discover and order food from various restaurants.",
        url=f"{public_url}",
        version="1.0.0",
        defaultInputModes=SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[food_ordering_skill],
    )
    return agent_card
