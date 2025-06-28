from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill
from common.task_manager import AgentTaskManager
from helper_bot_agent import HelperBotAgent
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host=os.environ.get("A2A_HOST", "localhost")
port=int(os.environ.get("A2A_PORT", 10004))
PUBLIC_URL=os.environ.get("PUBLIC_URL", "http://localhost:9992")

def main():
    """Loads the config and runs the A2A server for the personal helper bot agent."""
    try:
        capabilities = AgentCapabilities(streaming=True, tools=True, push_notifications=False)

        cuisine_discovery_skill = AgentSkill(
            id="cuisine-discovery",
            name="Discover Cuisines",
            description="Finds and suggests available cuisine options for the user to choose from.",
            tags=["food", "discovery", "cuisine"],
            examples=["What cuisines do you have?", "What are my food options?"],
        )

        food_selection_skill = AgentSkill(
            id="food-selection",
            name="Select Food Items",
            description="Shows available food items for a specific cuisine type.",
            tags=["food", "ordering", "menu"],
            examples=["What Italian dishes do you have?", "Show me Chinese food options"],
        )

        food_ordering_skill = AgentSkill(
            id="food-ordering",
            name="Order Food",
            description="Handles the complete food ordering process by connecting to the relevant restaurant.",
            tags=["food", "ordering", "delegation"],
            examples=["I want to order a pizza", "I would like to order some pasta" "Let's get some food!", "I'll have food please"],
        )

        agent_card = AgentCard(
            name="Alex Helper Bot",
            description="A friendly personal food ordering AI assistant that helps you discover and order food from various restaurants.",
            url=f"{PUBLIC_URL}",
            version="1.0.0",
            defaultInputModes=HelperBotAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=HelperBotAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[cuisine_discovery_skill, food_selection_skill, food_ordering_skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=HelperBotAgent()),
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
