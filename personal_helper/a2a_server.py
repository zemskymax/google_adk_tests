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
from agent_executor import HelperBotAgentExecutor
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from agent import helper_bot as agent
from agent_card import get_agent_card
from agent import agent_logic

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host=os.environ.get("A2A_HOST", "localhost")
port=int(os.environ.get("A2A_PORT", 10000))
public_url=os.environ.get("PUBLIC_URL", "http://localhost:10000")


class HelperBotAgent:
    """Loads the config and runs the A2A server for the personal helper agent."""

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
        """Returns the processing message for the personal helper agent."""
        return "Processing the food ordering request..."

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the personal helper agent."""
        return agent.root_agent


class AppWrapper:
    def __init__(self, app):
        self._app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await agent_logic._initialize()
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await send({'type': 'lifespan.shutdown.complete'})
                    return
        else:
            await self._app(scope, receive, send)


def main():
    """Loads the config and runs the A2A server for the personal helper agent."""
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

        app = CORSMiddleware(
            server.build(),
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        wrapped_app = AppWrapper(app)

        logger.info(f"Attempting to start server with Agent Card: {helper_agent.agent_card.name}")
        logger.info(f"Server object created: {server}")

        uvicorn.run(wrapped_app, host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)

if __name__ == "__main__":
    main()