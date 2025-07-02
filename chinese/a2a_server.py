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
from agent_executor import ChineseBotAgentExecutor
import uvicorn
from agent import chinese_food_bot as agent

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host=os.environ.get("A2A_HOST", "localhost")
port=int(os.environ.get("A2A_PORT", 10004))
public_url=os.environ.get("PUBLIC_URL", "http://localhost:10004")

class ChineseBotAgent:
    """Loads the config and runs the A2A server for the Chinese food bot agent."""

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

        order_food_skill = AgentSkill(
            id="order-chinese-food",
            name="Order Chinese Food",
            description="Adds a customized food item to the current order, specifying dishes and options.",
            tags=["ordering", "chinese", "food"],
            examples=["I'd like to order General Tso's Chicken.", "Can I get an order of spring rolls?"],
        )
        view_menu_skill = AgentSkill(
            id="view-menu",
            name="View Full Menu",
            description="Provides the entire menu, including appetizers, main courses, soups, and drinks.",
            tags=["menu", "information"],
            examples=["What's on your menu?", "Can you tell me what you have?"],
        )
        self.agent_card = AgentCard(
            name="Golden Dragon Bot",
            description="An AI assistant that represents a worker at the Golden Dragon Chinese Restaurant, ready to take your order.",
            url=f"{public_url}",
            version="1.0.0",
            defaultInputModes=ChineseBotAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=ChineseBotAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[order_food_skill, view_menu_skill],
        )

    def _build_agent(self) -> LlmAgent:
        return agent

def main():
    try:
        chinese_agent = ChineseBotAgent()

        request_handler = DefaultRequestHandler(
            agent_executor=ChineseBotAgentExecutor(chinese_agent.runner, chinese_agent.agent_card),
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(
            agent_card=chinese_agent.agent_card,
            http_handler=request_handler,
        )
        logger.info(f"Attempting to start server with Agent Card: {chinese_agent.agent_card.name}")

        uvicorn.run(server.build(), host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)

if __name__ == "__main__":
    main()
