from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill
from common.task_manager import AgentTaskManager
from pizza_bot_agent import PizzaBotAgent
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host=os.environ.get("A2A_HOST", "localhost")
port=int(os.environ.get("A2A_PORT", 10003))
PUBLIC_URL=os.environ.get("PUBLIC_URL", "http://localhost:9991")

def main():
    """Loads the config and runs the A2A server for the pizza bot agent."""
    try:
        capabilities = AgentCapabilities(streaming=True, tools=True, push_notifications=False)
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
            url=f"{PUBLIC_URL}",
            version="1.0.0",
            defaultInputModes=PizzaBotAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=PizzaBotAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[order_pizza_skill, view_menu_skill, calculate_bill_skill, get_eta_skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=PizzaBotAgent()),
            host=host,
            port=port,
        )
        logger.info(f"Attempting to start server with Agent Card: {agent_card.name}")
        logger.info(f"Server object created: {server}")

        server.start()
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)

if __name__ == "__main__":
    main()
