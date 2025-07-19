from a2a.types import AgentCard, AgentCapabilities, AgentSkill

SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

def get_agent_card(public_url: str) -> AgentCard:
    """Generates the agent card for the pizza bot agent."""
    capabilities = AgentCapabilities(streaming=False, tools=True, push_notifications=False)

    order_pizza_skill = AgentSkill(
        id="order-pizza",
        name="Order a Pizza",
        description="""Adds a customized pizza to the current order, specifying size, crust, and toppings.""",
        tags=["ordering", "pizza", "food"],
        examples=["I'd like a large pizza with thin crust and pepperoni.", "Can I get a medium deep dish with mushrooms and olives?"],
    )
    view_menu_skill = AgentSkill(
        id="view-menu",
        name="View Full Menu",
        description="""Provides the entire menu, including pizzas, sides, drinks, and combos.""",
        tags=["menu", "information"],
        examples=["What's on the menu?", "Can you tell me what pizzas you have?"],
    )
    calculate_bill_skill = AgentSkill(
        id="calculate-bill",
        name="Calculate Bill",
        description="""Calculates the subtotal, tax, and final total for the current order.""",
        tags=["billing", "payment", "checkout"],
        examples=["I'm ready to checkout.", "What's my total?"],
    )
    get_eta_skill = AgentSkill(
        id="get-eta",
        name="Get Order ETA",
        description="""Provides an estimated time of arrival (ETA) for a confirmed order.""",
        tags=["status", "delivery", "pickup"],
        examples=["When will my pizza be ready?", "What's the ETA for my delivery?"],
    )
    agent_card = AgentCard(
        name="Luigi's Pizza Bot",
        description="""An AI assistant that represents a worker at Luigi's Pizza House, ready to take your order.""",
        url=f"{public_url}",
        version="1.0.0",
        defaultInputModes=SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[order_pizza_skill, view_menu_skill, calculate_bill_skill, get_eta_skill],
    )
    return agent_card
