from a2a.server.apps import A2AStarletteApplication
from a2a.types import AgentCard, AgentCapabilities, AgentSkill
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
import os
import logging
from dotenv import load_dotenv
from .agent_executor import HelperBotAgentExecutor
import uvicorn
from .agent import helper_bot as agent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("personal_helper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

host=os.environ.get("A2A_HOST", "localhost")
port=int(os.environ.get("A2A_PORT", 10000))
public_url=os.environ.get("PUBLIC_URL", "http://localhost:10000")


class HelperBotAgent:
    """Loads the config and runs the A2A server for the helper agent."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self._agent = self._build_agent()
        self.runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

        capabilities = AgentCapabilities(streaming=False, tools=True, push_notifications=False)

        food_ordering_skill = AgentSkill(
            id="food-ordering",
            name="Order Food",
            description="Handles the complete food ordering process by discovering and connecting to the relevant restaurant.",
            tags=["food", "ordering", "delegation"],
            examples=["I want to order a pizza", "I would like to order some pasta", "Let's get some food!", "I'll have food please"],
        )

        self.agent_card = AgentCard(
            name="Alex Helper Bot",
            description="A friendly personal food ordering AI assistant that helps you discover and order food from various restaurants.",
            url=f"{public_url}",
            version="1.0.0",
            defaultInputModes=HelperBotAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=HelperBotAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[food_ordering_skill],
        )

    def get_processing_message(self) -> str:
        """Returns the processing message for the helper agent."""
        return "Processing the planning request..."

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the helper agent."""
        return agent.root_agent


def main():
    """Loads the config and runs the A2A server for the helper agent."""
    try:
        helper_agent = HelperBotAgent()

        request_handler = DefaultRequestHandler(
            agent_executor=HelperBotAgentExecutor(helper_agent.runner, helper_agent.agent_card),
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(
            agent_card=helper_agent.agent_card,
            http_handler=request_handler,
        )
        logger.info(f"Attempting to start server with Agent Card: {helper_agent.agent_card.name}")
        logger.info(f"Server object created: {server}")

        uvicorn.run(server.build(), host=host, port=port)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)

if __name__ == "__main__":
    main()
