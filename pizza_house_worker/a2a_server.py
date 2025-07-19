from a2a.server.apps import A2AStarletteApplication
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
from agent_executor import PizzaBotAgentExecutor
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from agent import pizza_bot as agent
from agent_card import get_agent_card

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host=os.environ.get("A2A_HOST", "localhost")
port=int(os.environ.get("A2A_PORT", 10003))
public_url=os.environ.get("PUBLIC_URL", "http://localhost:10003")


class PizzaBotAgent:
    """Loads the config and runs the A2A server for the pizza bot agent."""

    def __init__(self):
        self._agent = self._build_agent()
        self.runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        self.agent_card = get_agent_card(public_url)

    def get_processing_message(self) -> str:
        """Returns the processing message for the pizza bot agent."""
        return "Processing the pizza order request..."

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the night out planning agent."""
        return agent.root_agent


def main():
    """Loads the config and runs the A2A server for the pizza bot agent."""
    try:
        pizza_agent = PizzaBotAgent()

        request_handler = DefaultRequestHandler(
            agent_executor=PizzaBotAgentExecutor(pizza_agent.runner, pizza_agent.agent_card),
            task_store=InMemoryTaskStore(),
        )

        server = A2AStarletteApplication(
            agent_card=pizza_agent.agent_card,
            http_handler=request_handler,
        )

        app = CORSMiddleware(
            server.build(),
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # print("Available Endpoints:")
        # for route in app.app.routes:
        #     print(f"  - Path: {route.path}, Methods: {list(route.methods)}, Name: {route.name}")

        logger.info(f"Attempting to start server with Agent Card: {pizza_agent.agent_card.name}")
        logger.info(f"Server object created: {server}")

        uvicorn.run(app, host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)

if __name__ == "__main__":
    main()
