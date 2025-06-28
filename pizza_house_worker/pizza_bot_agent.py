from typing import Any, AsyncIterable, Dict, Optional
from google.adk.agents import LoopAgent
# from google.adk.tools.tool_context import ToolContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from common.task_manager import AgentWithTaskManager
from agent import pizza_bot


class PizzaBotAgent(AgentWithTaskManager):
    """An agent to help user ordering a pizza."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = "remote_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def get_processing_message(self) -> str:
        return "Processing the pizza order request..."

    def _build_agent(self) -> LoopAgent:
        """Builds the LLM agent for the pizza bot agent."""
        return pizza_bot
